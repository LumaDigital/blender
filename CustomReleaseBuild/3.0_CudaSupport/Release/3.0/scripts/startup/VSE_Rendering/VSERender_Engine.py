import os
import subprocess

import bpy

class Rendering_Engine():

    _BLENDER_COMPOSITING_BACK_EXR_OUTPUT_NODE_NAME = "Back_EXR_Output"
    _BLENDER_COMPOSITING_ACTORS_EXR_OUTPUT_NODE_NAME = "Actors_EXR_Output"
    _BLENDER_COMPOSITING_UVS_EXR_OUTPUT_NODE_NAME = "UVs_EXR_Output"

    _RENDER_RESOLUTION_X = 1280
    _RENDER_RESOLUTION_Y = 720

    _VV_MULTI_COMP_NAME = "MultiCompVV.py"
    _VV_COMP_NAME = "compvv.exe"
    _VV_MAKE_NAME = "makevv.exe"

    _vv_tools_path = None
    _multi_comp_vv_path = None 
    _comp_vv_path = None
    _make_vv_path = None

    _exr_output_path = None
    _png_output_path = None
    _vision_video_output_path = None

    _frame_start = 1
    _frame_end = 300
    _frame_rate = 30

    _max_render_samples = 128
    _min_render_samples = 1 # UV has no light data, therefore uses low sampling

    _exr_render = True
    _exr_back = True
    _exr_actors = True
    _exr_uvs = True
    _composite = True
    _make_vv = True

    _current_EXR_render_name = None

    def __init__(self,
                _exr_output_path,
                _png_output_path,
                _vision_video_output_path,
                _frame_start,
                _frame_end,
                _frame_rate,
                _max_render_samples,
                _exr_render,
                _exr_back,
                _exr_actors,
                _exr_uvs,
                _composite,
                _make_vv):

        self._exr_output_path = _exr_output_path
        self._png_output_path = _png_output_path
        self._vision_video_output_path = _vision_video_output_path
        self._frame_start = _frame_start
        self._frame_end = _frame_end
        self._frame_rate = _frame_rate
        self._max_render_samples = _max_render_samples
        self._exr_render = _exr_render
        self._exr_back = _exr_back
        self._exr_actors = _exr_actors
        self._exr_uvs = _exr_uvs
        self._composite = _composite
        self._make_vv = _make_vv

    def render_and_composite(self):

        print("\n=====================================================================================")
        print("VSE Render Automation\n")

        self.log_inputs()
        self._setup_scene()

        if self._exr_render:
            if self._exr_back:
                self._setup_and_run_back_render()
            if self._exr_actors:
                self._setup_and_run_actors_render()
            if self._exr_uvs:
                self._setup_and_run_uvs_render()
        
        if self._check_for_tools():
            if self._composite:
                self._initialize_comp_vv()
            if self._make_vv:
                self._initialize_make_vv()

        print("\n=====================================================================================")
        print ("\nRender processes completed successfully")    


    def log_inputs(self):

        print ("\nRecorded Inputs: ")
        print ("_exr_output_path: " + self._exr_output_path)
        print ("_png_output_path: " + self._png_output_path)
        print ("_vision_video_output_path: " + self._vision_video_output_path)
        print ("_max_render_samples: " + str(self._max_render_samples))
        print ("_frame_start: " + str(self._frame_start))
        print ("_frame_end: " + str(self._frame_end))
        print ("_frame_rate: " + str(self._frame_rate))
        print ("Render Options:")
        print ("EXRS: " + str(self._exr_render))
        
        if self._exr_render: 
            print("\tBack: " + str(self._exr_back))
            print("\tActors: " + str(self._exr_actors))
            print("\tUVs: " + str(self._exr_uvs))
            
        print ("PNGs: " + str(self._composite))
        print ("VV: " + str(self._make_vv))
        
        binary_path = os.path.dirname(bpy.app.binary_path)
        self._vv_tools_path = os.path.join(binary_path, "VVTools")

    def _setup_scene(self):
        bpy.context.scene.frame_start = self._frame_start
        bpy.context.scene.frame_end = self._frame_end
        bpy.context.scene.render.fps = self._frame_rate

    def set_resolution(self, resolution_x, resolution_y):
        bpy.context.scene.render.resolution_x = resolution_x
        bpy.context.scene.render.resolution_y = resolution_y

    def _pre_render_handle(self):
        print("\n=============== " + self._current_EXR_render_name + " EXR renders initialized")
        print("Frame Range: " + str(self._frame_start) + "-" + str(self._frame_end) + "\n")
        
    def _render_complete_handle(self):
        print("\nOutput path: " + self._exr_output_path)
        print("=============== " + self._current_EXR_render_name + " EXR renders complete")

    def _setup_and_run_back_render(self):  
        self._current_EXR_render_name = "Back"     
        self.set_resolution(self._RENDER_RESOLUTION_X, self._RENDER_RESOLUTION_Y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.context.scene.node_tree.nodes[
            self._BLENDER_COMPOSITING_BACK_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(self._exr_output_path, "Back_####.exr")
        self._pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self._render_complete_handle()

    def _setup_and_run_actors_render(self): 
        self._current_EXR_render_name = "Actors"         
        self.set_resolution(self._RENDER_RESOLUTION_X, self._RENDER_RESOLUTION_Y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.context.scene.node_tree.nodes[
            self._BLENDER_COMPOSITING_ACTORS_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(self._exr_output_path, "Actors_####.exr")
        self._pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self._render_complete_handle()

    def _setup_and_run_uvs_render(self): 
        self._current_EXR_render_name = "UV"          
        self.set_resolution(self._RENDER_RESOLUTION_X * 5, self._RENDER_RESOLUTION_Y * 5)
        bpy.context.scene.cycles.samples = self._min_render_samples
        bpy.context.scene.node_tree.nodes[
            self._BLENDER_COMPOSITING_UVS_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(self._exr_output_path, "UV_####.exr")
        self._pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self._render_complete_handle()

    def _check_for_tools(self):   
        tools_missing = ""       
        self._multi_comp_vv_path = os.path.join(self._vv_tools_path, self._VV_MULTI_COMP_NAME)
        print(self._multi_comp_vv_path)  
        if not os.path.exists(self._multi_comp_vv_path):
            tools_missing += "\t" + self._VV_MULTI_COMP_NAME
            
        self._comp_vv_path = os.path.join(self._vv_tools_path, self._VV_COMP_NAME)
        if not os.path.exists(self._comp_vv_path):
            tools_missing += "\t" + self._VV_COMP_NAME
            
        self._make_vv_path = os.path.join(self._vv_tools_path, self._VV_MAKE_NAME)
        if not os.path.exists(self._make_vv_path):
            tools_missing += "\t" + self._VV_MAKE_NAME
            
        if tools_missing != "":
            print("\n\n=====================================================================================")
            print("VSE ERROR:\nMissing VV tools: " + tools_missing)
            print("\n\nGet the all VV tools (MultiCompVV, CompVV, MakeVV) and put them in this directory:\n" + self._vv_tools_path)
            print("=====================================================================================\n\n")
            return False
        else:
            return True

    def _initialize_comp_vv(self):
        
        print("\n=====================================================================================")
        print("\nVision Video Compositing tools initialized:")
               
        frame_range = str(self._frame_start) + "-" + str(self._frame_end)        
        process = subprocess.Popen(
            [
                "python",
                self._multi_comp_vv_path,
                "-i", 
                self._exr_output_path, 
                "-o", 
                self._png_output_path,
                "-f",
                frame_range,
                "-c",
                self._comp_vv_path
                
            ])
        
        process.communicate()
        
    def _initialize_make_vv(self):
        
        print("\n=====================================================================================")
        print("\nMake Vision Video tool initialized:")
        
        # TODO: Change name based on cutscene name
        vv_file_name = os.path.join(self._vision_video_output_path, "Cutscene.vv")
        print("Output: " + vv_file_name)
        
        process = subprocess.Popen(
            [
                self._make_vv_path,
                "-o", 
                vv_file_name,
                "-dir",
                self._png_output_path,
                "-type",
                "VP8_UV20M4L8",
                "-start",
                str(self._frame_start)
                
            ])
        
        process.communicate()
