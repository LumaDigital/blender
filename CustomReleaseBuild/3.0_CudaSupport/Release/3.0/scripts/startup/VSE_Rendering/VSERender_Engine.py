import os
import subprocess
import time

import bpy

class Rendering_Engine():

    # We only use composite outputs, but Blender still renders frames to the scene's output.
    # To avoid overwriting artists' preview renders, this output will be changed to a temp dir.
    _TEMP_OUTPUT_PATH = "N:\\Blender\\TempRenders\\"
    _FFMPEG_RELATIVE_PATH = "FFMPEG\\bin\\ffmpeg.exe"

    _BLENDER_COMPOSITING_BACK_EXR_OUTPUT_NODE_NAME = "Back_EXR_Output"
    _BLENDER_COMPOSITING_ACTORS_EXR_OUTPUT_NODE_NAME = "Actors_EXR_Output"
    _BLENDER_COMPOSITING_UVS_EXR_OUTPUT_NODE_NAME = "UVs_EXR_Output"

    _RENDER_RESOLUTION_X = 1280
    _RENDER_RESOLUTION_Y = 720

    _VV_MULTI_COMP_NAME = "MultiCompVV.py"
    _VV_COMP_NAME = "compvv.exe"
    _VV_MAKE_NAME = "makevv.exe"
    _VV_VIEWER_FOLDER_NAME = "VisionViewer"

    _VISION_VIEWER_RANDOM_BAT_PREFIX = "Play_"

    _vv_tools_path = None
    _multi_comp_vv_path = None 
    _comp_vv_path = None
    _make_vv_path = None
    _ffmpeg_path = None
    _vision_viewer_dir = None

    _exr_output_path = None
    _png_output_path = None
    _vision_video_output_path = None

    _frame_start = 1
    _frame_end = 300
    _frame_rate = 30

    _max_render_samples = 128
    _min_render_samples = 1 # UV has no light data, therefore uses low sampling

    _exr_back = False
    _exr_actors = False
    _exr_uvs = False
    _composite = False
    _make_vv = False

    def __init__(self,
                _exr_output_path,
                _png_output_path,
                _vision_video_output_path,
                _frame_start,
                _frame_end,
                _frame_rate,
                _max_render_samples,
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
        self._exr_back = _exr_back
        self._exr_actors = _exr_actors
        self._exr_uvs = _exr_uvs
        self._composite = _composite
        self._make_vv = _make_vv

    def render_and_composite(self):

        print("\n=====================================================================================")
        print("VSE Render Automation")

        self.handle_temp_output();
        self.log_inputs()
        self._setup_scene()

        _render_back_actors = False
        if self._exr_back:
            bpy.context.scene.view_layers["Back"].use = True
            _render_back_actors = True
            self._setup_back_render()
        if self._exr_actors:
            bpy.context.scene.view_layers["Actors"].use = True
            _render_back_actors = True
            self._setup_actors_render()

        if _render_back_actors:
            print("\nRendering Back/Actors EXRs:\n")
            bpy.context.scene.view_layers["UV"].use = False
            bpy.ops.render.render(animation=True)

        if self._exr_uvs:
            print("\nRendering UV EXRs:\n")
            self._setup_uvs_render()
            bpy.context.scene.view_layers["UV"].use = True
            bpy.context.scene.view_layers["Back"].use = False
            bpy.context.scene.view_layers["Actors"].use = False
            bpy.ops.render.render(animation=True)
        
        if self._check_for_tools():
            if self._composite:
                self._initialize_comp_vv()
            if self._make_vv:
                #self._initialize_make_vv()
                self._record_vision_video_preview()

        print("\n=====================================================================================")
        print ("\nRender processes completed successfully")    

    def handle_temp_output(self):

        if (os.path.exists(self._TEMP_OUTPUT_PATH)):
            bpy.context.scene.render.filepath = self._TEMP_OUTPUT_PATH
        else:
            print("\n=====================================================================================")
            print ("\nWARNING: Add a temporary directory to the N drive:" + self._TEMP_OUTPUT_PATH + " to avoid overwriting " +
                   "the output file in the blend scene")
            print("\n=====================================================================================")

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
        print("Render Back EXRs: " + str(self._exr_back))
        print("Render Actors EXRs: " + str(self._exr_actors))
        print("Render UVs EXRs: " + str(self._exr_uvs))   
        print ("PNGs: " + str(self._composite))
        print ("VV: " + str(self._make_vv))
        
        binary_path = os.path.dirname(bpy.app.binary_path)
        self._vv_tools_path = os.path.join(binary_path, "VVTools")
        self._ffmpeg_dir = os.path.join(binary_path, self._FFMPEG_RELATIVE_PATH)

    def _setup_scene(self):
        bpy.context.scene.render.use_single_layer = False
        bpy.context.scene.frame_start = self._frame_start
        bpy.context.scene.frame_end = self._frame_end
        bpy.context.scene.render.fps = self._frame_rate

    def set_resolution(self, resolution_x, resolution_y):
        bpy.context.scene.render.resolution_x = resolution_x
        bpy.context.scene.render.resolution_y = resolution_y

    def _setup_back_render(self):     
        self.set_resolution(self._RENDER_RESOLUTION_X, self._RENDER_RESOLUTION_Y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.context.scene.node_tree.nodes[
            self._BLENDER_COMPOSITING_BACK_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(self._exr_output_path, "Back_####.exr")

    def _setup_actors_render(self):         
        self.set_resolution(self._RENDER_RESOLUTION_X, self._RENDER_RESOLUTION_Y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.context.scene.node_tree.nodes[
            self._BLENDER_COMPOSITING_ACTORS_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(self._exr_output_path, "Actors_####.exr")

    def _setup_uvs_render(self):          
        self.set_resolution(self._RENDER_RESOLUTION_X * 5, self._RENDER_RESOLUTION_Y * 5)
        bpy.context.scene.cycles.samples = self._min_render_samples
        bpy.context.scene.node_tree.nodes[
            self._BLENDER_COMPOSITING_UVS_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(self._exr_output_path, "UV_####.exr")

    def _check_for_tools(self):   
        tools_missing = ""       
        self._multi_comp_vv_path = os.path.join(self._vv_tools_path, self._VV_MULTI_COMP_NAME)
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
            print("\n\nGet all VV tools (MultiCompVV, CompVV, MakeVV) and put them in this directory:\n" + self._vv_tools_path)
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

    def _record_vision_video_preview(self):
        print("\n=====================================================================================")
        print("\nVideo Capture initialized:")

        if self._get_recording_tools():

            #process = subprocess.Popen(
            #    self._VISION_VIEWER_RANDOM_BAT_PREFIX + "1.bat",
            #    stdout=subprocess.PIPE,
            #    shell=True,
            #    cwd=r"{}".format(self._vision_viewer_dir))

            process = subprocess.Popen(
            [
                "E:\\MartinWork\\OpenSource\\blender\\CustomReleaseBuild\\3.0_CudaSupport\\Release\\VVTools\\VisionViewer\\VisionViewer.exe",
                "CricketSuperOver",
                "DemoFile='Demo\Random_1.cfg'",
                "DemoFirstEventSeconds=0",
                "Debug",
                "Max30"          
            ])

            #process.communicate()
            time.sleep(10)
            process.kill()
            #print("should be dead")
            #process.terminate()


    def _get_recording_tools(self):

        ffmpeg_missing = False     
        if not os.path.exists(self._ffmpeg_dir):
            ffmpeg_missing = True
                     
        if ffmpeg_missing:
            print("\n\n=====================================================================================")
            print("VSE ERROR:\nMissing FFMPEG tool ")
            print("\nFFMPEG should be added here:\n" + self._ffmpeg_dir)
            print("=====================================================================================\n\n")
            return False

        vision_viewer_missing = False     
        self._vision_viewer_dir = os.path.join(self._vv_tools_path, self._VV_VIEWER_FOLDER_NAME)
        if not os.path.exists(self._vision_viewer_dir):
            vision_viewer_missing = True
                     
        if vision_viewer_missing:
            print("\n\n=====================================================================================")
            print("VSE ERROR:\nMissing Vision Viewer tool")
            print("\nVision Viewer should be added here:\n" + self._vision_viewer_dir)
            print("=====================================================================================\n\n")
            return False

        return True;
