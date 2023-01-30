import bpy
import os
import subprocess

class VSELookDev(bpy.types.Operator):
    
    """Renders 3 compulsory EXRs (Back, Actors, UVs), composites them with CompVV, and then sequences those images with MakeVV to the specified path"""
    
    bl_idname = "vse.render"
    bl_label = "VSE Render Operator"
    
    vv_multi_comp_name = "MultiCompVV.py"
    vv_comp_name = "compvv.exe"
    vv_make_name = "makevv.exe"
    
    _vv_tools_path = None
    _multi_comp_vv_path = None 
    _comp_vv_path = None
    _make_vv_path = None
         
    _fbx_actor_path = None
    _exr_output_path = None
    _png_output_path = None
    _vision_video_output_path = None
        
    _srt_obj = None;
    _import_obj = None;
    
    _background_items = ["shoes"]  
    _team_one_material_name = "Player_01_Mat"
    _team_two_material_name = "Player_02_Mat"
    _selected_team_material_name = _team_one_material_name
    _background_material_name = "Player_01_Shoe_Mat" # Need to change material name to something more appropriate
    
    _render_resolution_x = 1280
    _render_resolution_y = 720
    
    _max_render_samples = 128
    _min_render_samples = 1 # UV has not light data, therefore uses low sampling
     
    _frame_start = 1
    _frame_end = 300
    _frame_rate = 30
    
    _current_EXR_render_name = None

    def execute(self, context):
        
        self.initialization_text()
        self.assign_ui_variables()
        self.setup_scene()
        self.handle_import()
        self.setup_and_run_back_render()
        self.setup_and_run_actors_render()
        self.setup_and_run_uvs_render()
        
        if (self.check_for_tools()):
            self.initialize_comp_vv()
            self.initialize_make_vv()
            
        print ("\nLookDev Render completed Successfully")    

        return {"FINISHED"}
       
        
    def initialization_text(self):
        print("\n=====================================================================================")
        print("VSE Look Dev Automation\n")  
        
    def assign_ui_variables(self):
        self._fbx_actor_path = bpy.context.scene.lookdev_actor_import_file_path
        self._exr_output_path = bpy.context.scene.lookdev_exr_output_path 
        self._vision_video_output_path = bpy.context.scene.lookdev_vision_video_output_path
        self._frame_start = bpy.context.scene.lookdev_frame_start
        self._frame_end = bpy.context.scene.lookdev_frame_end   
        self._png_output_path = bpy.context.scene.lookdev_png_output_path
        self._max_render_samples = bpy.context.scene.lookdev_max_render_samples
        self._frame_rate = bpy.context.scene.lookdev_frame_rate
        
        print ("\nRecorded Inputs: ")
        print ("_fbx_actor_path: " + self._fbx_actor_path)
        print ("_exr_output_path: " + self._exr_output_path)
        print ("_png_output_path: " + self._png_output_path)
        print ("_vision_video_output_path: " + self._vision_video_output_path)
        print ("_max_render_samples: " + str(self._max_render_samples))
        print ("_frame_start: " + str(self._frame_start))
        print ("_frame_end: " + str(self._frame_end))
        print ("_frame_rate: " + str(self._frame_rate))
        
        binary_path = os.path.dirname(bpy.app.binary_path)
        self._vv_tools_path = os.path.join(binary_path, "VVTools")        
        
    def setup_scene(self):
        bpy.context.scene.frame_start = self._frame_start
        bpy.context.scene.frame_end = self._frame_end
        bpy.context.scene.render.fps = self._frame_rate

         
    def handle_import(self):     
        self._srt_obj = bpy.data.objects["Main_SRT"]
        print ("\nImporting Actor FBX:\n" + self._fbx_actor_path)  
        bpy.ops.import_scene.fbx(filepath=self._fbx_actor_path)
        self._import_obj = bpy.context.view_layer.objects.active
        self._import_obj.parent = self._srt_obj
        self.assign_team_material()
        
    def assign_team_material(self):
        self.assign_materials_to_children_recursive(self._import_obj, bpy.data.materials[self._selected_team_material_name])
        bpy.data.materials[self._selected_team_material_name].node_tree.nodes["Mix.001"].inputs[0].default_value = 0 # Node name has been change but the action still returns "Mix.001"
    
    def set_resolution(self, resolution_x, resolution_y):
        bpy.context.scene.render.resolution_x = resolution_x
        bpy.context.scene.render.resolution_y = resolution_y
    
    def setup_and_run_back_render(self):  
        self._current_EXR_render_name = "Back"     
        self.set_resolution(self._render_resolution_x, self._render_resolution_y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.data.materials[self._selected_team_material_name].node_tree.nodes["Mix"].inputs[0].default_value = 1
        bpy.context.scene.node_tree.nodes['File Output.003'].base_path = os.path.join(self._exr_output_path, "Back_####.exr")
        self.pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self.render_complete_handle()
        
    def setup_and_run_actors_render(self): 
        self._current_EXR_render_name = "Actors"         
        self.set_resolution(self._render_resolution_x, self._render_resolution_y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.data.materials[self._selected_team_material_name].node_tree.nodes["Mix"].inputs[0].default_value = 0
        bpy.context.scene.node_tree.nodes['Actors'].base_path = os.path.join(self._exr_output_path, "Actors_####.exr")
        self.pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self.render_complete_handle()
        
    def setup_and_run_uvs_render(self): 
        self._current_EXR_render_name = "UV"          
        self.set_resolution(self._render_resolution_x * 5, self._render_resolution_y * 5)
        bpy.context.scene.cycles.samples = self._min_render_samples
        bpy.context.scene.node_tree.nodes['File Output.004'].base_path = os.path.join(self._exr_output_path, "UV_####.exr")
        self.pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self.render_complete_handle()
        
    def initialize_comp_vv(self):
        
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
        
    def initialize_make_vv(self):
        
        print("\n=====================================================================================")
        print("\nMake Vision Video tool initialized:")
        
        vv_file_name = os.path.join(self._vision_video_output_path, "LookDev.vv")
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
               
        
    def check_for_tools(self):
        
        tools_missing = ""       
        self._multi_comp_vv_path = os.path.join(self._vv_tools_path, self.vv_multi_comp_name)
        print(self._multi_comp_vv_path)  
        if not os.path.exists(self._multi_comp_vv_path):
            tools_missing += "\t" + self.vv_multi_comp_name
            
        self._comp_vv_path = os.path.join(self._vv_tools_path, self.vv_comp_name)
        if not os.path.exists(self._comp_vv_path):
            tools_missing += "\t" + self.vv_comp_name
            
        self._make_vv_path = os.path.join(self._vv_tools_path, self.vv_make_name)
        if not os.path.exists(self._make_vv_path):
            tools_missing += "\t" + self.vv_make_name
            
        if tools_missing != "":
            print("\n\n=====================================================================================")
            print("VSE ERROR:\nMissing VV tools: " + tools_missing)
            print("\n\nGet the all VV tools (MultiCompVV, CompVV, MakeVV) and put them in this directory:\n" + self._vv_tools_path)
            print("=====================================================================================\n\n")
            return False
        else:
            return True
        
            
    def assign_materials_to_children_recursive(self, obj, material):
        
        background_material = bpy.data.materials[self._background_material_name]
        
        for child in obj.children:          
            bpy.context.view_layer.objects.active = child  
                    
            if (bpy.context.view_layer.objects.active.data is not None):
                
                if any(substring in child.name.lower() for substring in self._background_items): # is background item
                    bpy.context.view_layer.objects.active.data.materials[0] = background_material
                else:
                    bpy.context.view_layer.objects.active.data.materials[0] = material
                    bpy.context.view_layer.objects.active.pass_index = 1
                
            self.assign_materials_to_children_recursive(child, material)
            
    def pre_render_handle(self):
        print("\n=============== " + self._current_EXR_render_name + " EXR renders initialized")
        print("Frame Range: " + str(self._frame_start) + "-" + str(self._frame_end) + "\n")
        
    def render_complete_handle(self):
        print("\nOutput path: " + self._exr_output_path)
        print("=============== " + self._current_EXR_render_name + " EXR renders complete")
        
class OT_ImportFBX(bpy.types.Panel):
    bl_label = "VSE LookDev"
    bl_idname = "LD_PT_TestPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LookDev'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text = "VV Actors setup and render tool", icon = 'INFO')
        scn = bpy.context.scene
        layout.row().separator(factor=2)
        row = layout.row()
        row.prop(scn, "lookdev_actor_import_file_path" )
        row = layout.row()
        row.prop(scn, "lookdev_exr_output_path")
        row = layout.row()
        row.prop(scn, "lookdev_png_output_path")
        row = layout.row()
        row.prop(scn, "lookdev_vision_video_output_path")
        row = layout.row()
        row.prop(scn, "lookdev_frame_start" )
        row = layout.row()
        row.prop(scn, "lookdev_frame_end" )
        row = layout.row()
        row.prop(scn, "lookdev_frame_rate")
        row = layout.row()
        row.prop(scn, "lookdev_max_render_samples")
        
        layout.row().separator(factor=5)
        col = layout.column(align=True)
        col.operator("vse.render", text="Render and Composite")

        layout.separator()

# Blender Validation
def register():
    bpy.utils.register_class(OT_ImportFBX)
    bpy.utils.register_class(VSELookDev)
    
def unregister():
    bpy.utils.unregister_class(OT_ImportFBX)
    bpy.utils.unregister_class(VSELookDev)
    
def assign_control_variables():
    
    bpy.types.Scene.lookdev_actor_import_file_path  = ( 
        bpy.props.StringProperty(name = "FBX Path", description = "FBX Import File Path", subtype = "FILE_PATH", update = validateFBXPath))
    bpy.types.Scene.lookdev_exr_output_path  = ( 
        bpy.props.StringProperty(name = "EXR Out Path", description = "Where Back, Actors and UV renders go", subtype = "FILE_PATH"))
    bpy.types.Scene.lookdev_png_output_path  = ( 
        bpy.props.StringProperty(name = "PNG Out Path", description = "Where composited PNGs go", subtype = "FILE_PATH"))
    bpy.types.Scene.lookdev_vision_video_output_path  = ( 
        bpy.props.StringProperty(name = "VV Out Path", description = "Where the Vision Video file goes", subtype = "FILE_PATH"))    
           
    bpy.types.Scene.lookdev_frame_start  = ( 
        bpy.props.IntProperty(name = "Start Frame: ", min=1))
    bpy.types.Scene.lookdev_frame_end  = ( 
        bpy.props.IntProperty(name = "End Frame: ", default=300, max=300))
    bpy.types.Scene.lookdev_frame_rate  = ( 
        bpy.props.IntProperty(name = "Frame Rate: ", default=30))
    bpy.types.Scene.lookdev_max_render_samples  = ( 
        bpy.props.IntProperty(name = "Actors/Back render sample: ", default=128))
        
def validateFBXPath(self, context):
    actor_file_path = bpy.context.scene.lookdev_actor_import_file_path
    if (actor_file_path[-3:] != "fbx" and actor_file_path != " "):
        ShowMessageBox("Please import an FBX file", "File not FBX!", 'ERROR')
        bpy.context.scene.lookdev_actor_import_file_path = " "# To avoid recursion error, use double empty
        return
        
def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
        
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
     
# This script is run automatically from startup folder, blender calls register on all start up scripts, 
# therefore calling register from the script is unecessary unless the script
# is manually run through Blender
if __name__ == "__main__":
    register()
    
assign_control_variables()
