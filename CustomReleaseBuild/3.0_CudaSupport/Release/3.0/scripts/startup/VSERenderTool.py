import bpy
import subprocess
import os

class Load_Render_Ready_Blender(bpy.types.Operator):
    """Loads the default render ready blend scene"""
    bl_idname = "vse.render_load"
    bl_label = "VSE Render blend loadOperator"
    
    _render_ready_blend_path = None
    
    def execute(self, context):
        
        self._initialization_text()
        self._assign_ui_variables()
        self._load_blend()  
        return {"FINISHED"}
    
    def _load_blend(self):
        print("\nLoading render ready blend file")
        bpy.ops.wm.open_mainfile(filepath=self._render_ready_blend_path)
        print("Success")
    
    def _initialization_text(self):
        print("\n=====================================================================================")
        print("VSE Render Automation\n")  
        
    def _assign_ui_variables(self):
        self._render_ready_blend_path = bpy.context.scene.vse_render_blend_path 
        
        print ("\nRecorded Inputs: ")
        print ("_render_ready_blend_path: " + self._render_ready_blend_path)

class Render_And_Composite(bpy.types.Operator):
    """Renders 3 compulsory EXRs (Back, Actors, UVs), composites them with CompVV, and then sequences those images with MakeVV to the specified path"""
    bl_idname = "vse.render"
    bl_label = "VSE Render Operator"
    
    _vv_multi_comp_name = "MultiCompVV.py"
    _vv_comp_name = "compvv.exe"
    _vv_make_name = "makevv.exe"
    
    _background_items = ["shoes"] 
    _background_material_name = "Player_01_Shoe_Mat" # Need to change material name to something more appropriate

    _team_one_material_name = "Player_01_Mat"
    _team_two_material_name = "Player_02_Mat"
    
    _vv_tools_path = None
    _multi_comp_vv_path = None 
    _comp_vv_path = None
    _make_vv_path = None
         
    _exr_output_path = None
    _png_output_path = None
    _vision_video_output_path = None
       
    _render_resolution_x = 1280
    _render_resolution_y = 720
    
    _max_render_samples = 128
    _min_render_samples = 1 # UV has no light data, therefore uses low sampling
     
    _frame_start = 1
    _frame_end = 300
    _frame_rate = 30
    
    _exr_render = True
    _exr_back = True
    _exr_actors = True
    _exr_uvs = True
    _composite = True
    _make_vv = True
    
    _current_EXR_render_name = None

    def execute(self, context):
        
        self._initialization_text()
        self._assign_ui_variables()
        self._setup_scene()
        self._setup_actors()
        
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

        return {"FINISHED"}
       
        
    def _initialization_text(self):
        print("\n=====================================================================================")
        print("VSE Render Automation\n")  
        
    def _assign_ui_variables(self):
        self._exr_output_path = bpy.context.scene.vse_exr_output_path 
        self._vision_video_output_path = bpy.context.scene.vse_vision_video_output_path
        self._frame_start = bpy.context.scene.vse_frame_start
        self._frame_end = bpy.context.scene.vse_frame_end   
        self._png_output_path = bpy.context.scene.vse_png_output_path
        self._max_render_samples = bpy.context.scene.vse_max_render_samples
        self._frame_rate = bpy.context.scene.vse_frame_rate
        self._exr_render = bpy.context.scene.vse_exr_render    
        self._exr_back = bpy.context.scene.vse_exr_back
        self._exr_actors = bpy.context.scene.vse_exr_actors
        self._exr_uvs = bpy.context.scene.vse_exr_uvs
        self._composite = bpy.context.scene.vse_composite
        self._make_vv = bpy.context.scene.vse_make_vv
        
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
    
    def _setup_and_run_back_render(self):  
        self._current_EXR_render_name = "Back"     
        self.set_resolution(self._render_resolution_x, self._render_resolution_y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.data.materials[self._team_one_material_name].node_tree.nodes["Mix"].inputs[0].default_value = 1
        bpy.data.materials[self._team_two_material_name].node_tree.nodes["Mix"].inputs[0].default_value = 1
        bpy.context.scene.node_tree.nodes['File Output.003'].base_path = os.path.join(self._exr_output_path, "Back_####.exr")
        self.pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self.render_complete_handle()
        
    def _setup_and_run_actors_render(self): 
        self._current_EXR_render_name = "Actors"         
        self.set_resolution(self._render_resolution_x, self._render_resolution_y)
        bpy.context.scene.cycles.samples = self._max_render_samples
        bpy.data.materials[self._team_one_material_name].node_tree.nodes["Mix"].inputs[0].default_value = 0
        bpy.data.materials[self._team_two_material_name].node_tree.nodes["Mix"].inputs[0].default_value = 0
        bpy.context.scene.node_tree.nodes['Actors'].base_path = os.path.join(self._exr_output_path, "Actors_####.exr")
        self.pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self.render_complete_handle()
        
    def _setup_and_run_uvs_render(self): 
        self._current_EXR_render_name = "UV"          
        self.set_resolution(self._render_resolution_x * 5, self._render_resolution_y * 5)
        bpy.context.scene.cycles.samples = self._min_render_samples
        bpy.context.scene.node_tree.nodes['File Output.004'].base_path = os.path.join(self._exr_output_path, "UV_####.exr")
        self.pre_render_handle()
        bpy.ops.render.render(animation=True, layer=self._current_EXR_render_name)
        self.render_complete_handle()
        
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
               
        
    def _check_for_tools(self):
        
        tools_missing = ""       
        self._multi_comp_vv_path = os.path.join(self._vv_tools_path, self._vv_multi_comp_name)
        print(self._multi_comp_vv_path)  
        if not os.path.exists(self._multi_comp_vv_path):
            tools_missing += "\t" + self._vv_multi_comp_name
            
        self._comp_vv_path = os.path.join(self._vv_tools_path, self._vv_comp_name)
        if not os.path.exists(self._comp_vv_path):
            tools_missing += "\t" + self._vv_comp_name
            
        self._make_vv_path = os.path.join(self._vv_tools_path, self._vv_make_name)
        if not os.path.exists(self._make_vv_path):
            tools_missing += "\t" + self._vv_make_name
            
        if tools_missing != "":
            print("\n\n=====================================================================================")
            print("VSE ERROR:\nMissing VV tools: " + tools_missing)
            print("\n\nGet the all VV tools (MultiCompVV, CompVV, MakeVV) and put them in this directory:\n" + self._vv_tools_path)
            print("=====================================================================================\n\n")
            return False
        else:
            return True
    
    def pre_render_handle(self):
        print("\n=============== " + self._current_EXR_render_name + " EXR renders initialized")
        print("Frame Range: " + str(self._frame_start) + "-" + str(self._frame_end) + "\n")
        
    def render_complete_handle(self):
        print("\nOutput path: " + self._exr_output_path)
        print("=============== " + self._current_EXR_render_name + " EXR renders complete")
    
    
    def _setup_actors(self):     
        print ("\nSetting up Actors:\n")
        
        geos_modified = ""
        for actor_obj in bpy.data.collections["TeamA"].objects:
            self._assign_team_material(actor_obj, self._team_one_material_name)
            geos_modified += actor_obj.name + "\t"
                
        for actor_obj in bpy.data.collections["TeamB"].objects:
            self._assign_team_material(actor_obj, self._team_two_material_name)
            geos_modified += "\t" + actor_obj.name
        
        print("Actors' geos:\n" + geos_modified + "\n\nSuccessfully setup for vision video rendering")
            
    def _assign_team_material(self, actor, material_name):
        self._assign_materials_to_children_recursive(actor, bpy.data.materials[material_name])
        bpy.data.materials[material_name].node_tree.nodes["Mix.001"].inputs[0].default_value = 0 # Node name has been change but the action still returns "Mix.001"
        
    def _assign_materials_to_children_recursive(self, obj, material):
        
        background_material = bpy.data.materials[self._background_material_name]
        
        for child in obj.children:          
            bpy.context.view_layer.objects.active = child  
                    
            if (bpy.context.view_layer.objects.active.data is not None):
                
                if any(substring in child.name.lower() for substring in self._background_items): # is background item
                    bpy.context.view_layer.objects.active.data.materials[0] = background_material
                else:
                    bpy.context.view_layer.objects.active.data.materials[0] = material
                    bpy.context.view_layer.objects.active.pass_index = 1
                
            self._assign_materials_to_children_recursive(child, material)
            
    
class Render_Tool_Panel(bpy.types.Panel):
    bl_label = "VSE Render Tool"
    bl_idname = "LD_PT_RenderPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VSE Render'
    
    def draw(self, context):
        
        layout = self.layout
        scn = bpy.context.scene
        
        row = layout.row()
        row.label(text = "Vision Video setup, render, comp and sequencing tool")
        
        layout.row().separator(factor=2)
        row = layout.row()
        row.prop(scn, "vse_render_blend_path")
        col = layout.column(align=True)
        col.operator("vse.render_load", text="Load Render blend", icon="TIME")
        row = layout.row()
        row.prop(scn, "vse_exr_output_path")
        row = layout.row()
        row.prop(scn, "vse_png_output_path")
        row = layout.row()
        row.prop(scn, "vse_vision_video_output_path")
        row = layout.row()
        row.prop(scn, "vse_frame_start" )
        row = layout.row()
        row.prop(scn, "vse_frame_end" )
        row = layout.row()
        row.prop(scn, "vse_frame_rate")
        row = layout.row()
        row.prop(scn, "vse_max_render_samples")
    
        layout.row().separator(factor=3)
        row = layout.row()
        row.prop(scn, "vse_exr_render")
        
        row = layout.row()
        if bpy.context.scene.vse_exr_render:
            row.prop(scn, "vse_exr_back")
            row.prop(scn, "vse_exr_actors")
            row.prop(scn, "vse_exr_uvs")
        
        row = layout.row()
        row.prop(scn, "vse_composite")
        row = layout.row()
        row.prop(scn, "vse_make_vv")
        col = layout.column(align=True)
        col.operator("vse.render", text="Initialize", icon="TIME")
        row = layout.row()
        row.label(text = "Objects under 'TeamA/B' collections are handled as actors", icon = 'INFO')
        row = layout.row()
        row.label(text = "Initialize without any options to only setup actors", icon = 'INFO')

        layout.separator()

# Blender Validation
def register():
    bpy.utils.register_class(Render_Tool_Panel)
    bpy.utils.register_class(Render_And_Composite)
    bpy.utils.register_class(Load_Render_Ready_Blender)
    
def unregister():
    bpy.utils.unregister_class(Render_Tool_Panel)
    bpy.utils.unregister_class(Render_And_Composite)
    bpy.utils.unregister_class(Load_Render_Ready_Blender)
    
def assign_control_variables():
    
    bpy.types.Scene.vse_render_blend_path  = ( 
        bpy.props.StringProperty(
            name = "Render Blend Path",
            description = "Render ready blend file location. This blend has all actors set up correctly",
            subtype = "FILE_PATH",
            default = "N:\\Cricket\\assets\\BaseRenderBlend\\VSE_Cricket.blend",
            update = validate_blend_Path))
            
    bpy.types.Scene.vse_exr_output_path  = ( 
        bpy.props.StringProperty(name = "EXR Out Path", description = "Where Back, Actors and UV renders go", subtype = "FILE_PATH"))
    bpy.types.Scene.vse_png_output_path  = ( 
        bpy.props.StringProperty(name = "PNG Out Path", description = "Where composited PNGs go", subtype = "FILE_PATH"))
    bpy.types.Scene.vse_vision_video_output_path  = ( 
        bpy.props.StringProperty(name = "VV Out Path", description = "Where the Vision Video file goes", subtype = "FILE_PATH"))    
           
    bpy.types.Scene.vse_frame_start  = ( 
        bpy.props.IntProperty(name = "Start Frame: ", min=1, default=1))
    bpy.types.Scene.vse_frame_end  = ( 
        bpy.props.IntProperty(name = "End Frame: ", default=300))
    bpy.types.Scene.vse_frame_rate  = ( 
        bpy.props.IntProperty(name = "Frame Rate: ", default=30))
    bpy.types.Scene.vse_max_render_samples  = ( 
        bpy.props.IntProperty(name = "Actors/Back render sample: ", default=128))
        
    bpy.types.Scene.vse_exr_render = bpy.props.BoolProperty(name = "Render EXRs", default=True)
    
    bpy.types.Scene.vse_exr_back = bpy.props.BoolProperty(name = "Back", default=True)
    bpy.types.Scene.vse_exr_actors = bpy.props.BoolProperty(name = "Actors", default=True)
    bpy.types.Scene.vse_exr_uvs = bpy.props.BoolProperty(name = "UVs", default=True)
    
    bpy.types.Scene.vse_composite = bpy.props.BoolProperty(name = "Composite PNGs", default=True)
    bpy.types.Scene.vse_make_vv = bpy.props.BoolProperty(name = "Make Vision Video", default=True)
    
def validate_blend_Path(self, context):
    blend_file_path = bpy.context.scene.vse_render_blend_path
    if (blend_file_path[-5:] != "blend" and blend_file_path != " "):
        ShowMessageBox("Please select blend file", "File not Blend!", 'ERROR')
        bpy.context.scene.vse_render_blend_path = " "# To avoid recursion error, use double empty
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
