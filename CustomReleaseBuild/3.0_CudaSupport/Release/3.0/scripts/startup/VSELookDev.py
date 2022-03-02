import bpy
import os
import subprocess

class LookDev_Load(bpy.types.Operator):
    
    """Load the specified LookDev turntable blend"""
    
    bl_idname = "vse.lookdev_load"
    bl_label = "VSE LookDev load Operator"
    
    _blend_file_path = None
    
    def execute(self, context):
        
        self.initialization_text()
        self.assign_ui_variables()
        self.load_scene()

        return {"FINISHED"}
       
        
    def initialization_text(self):
        print("\n=====================================================================================")
        print("VSE Look Dev Automation\n")  
        
    def assign_ui_variables(self):
        self._blend_file_path = bpy.context.scene.lookdev_blend_file_path
        print ("\nRecorded Inputs: ")
        print ("_blend_file_path: " + self._blend_file_path)
           
    def load_scene(self):
        print("\nLoading turntable lookdev blend file")
        bpy.ops.wm.open_mainfile(filepath=self._blend_file_path)
        print("Success")
        
class LookDev_Setup(bpy.types.Operator):
    
    """Import and Setup FBX for LookDev and rendering"""
    
    bl_idname = "vse.lookdev_setup"
    bl_label = "VSE LookDev setup Operator"
    
    _srt_obj = None
    _import_obj = None
    _fbx_actor_path = None  

    def execute(self, context):
        
        self.initialization_text()
        self.assign_ui_variables()
        self.handle_import()

        return {"FINISHED"}
       
        
    def initialization_text(self):
        print("\n=====================================================================================")
        print("VSE Look Dev Automation\n")  
        
    def assign_ui_variables(self):
        self._fbx_actor_path = bpy.context.scene.lookdev_actor_import_file_path        
        print ("\nRecorded Inputs: ")
        print ("_fbx_actor_path: " + self._fbx_actor_path)   
           
    def handle_import(self):     
        self._srt_obj = bpy.data.objects["Main_SRT"]
        print ("\nImporting Actor FBX:\n" + self._fbx_actor_path)  
        bpy.ops.import_scene.fbx(filepath=self._fbx_actor_path)
        self._import_obj = bpy.context.view_layer.objects.active
        self._import_obj.parent = self._srt_obj
        bpy.data.collections['TeamA'].objects.link(self._import_obj)
        
class Render_Tool_Panel(bpy.types.Panel):
    bl_label = "VSE LookDev Tool"
    bl_idname = "LD_PT_TestPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VSE LookDev'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text = "Vision Video LookDev setup tool")
        scn = bpy.context.scene
        layout.row().separator(factor=2)
        row = layout.row()
        row.prop(scn, "lookdev_blend_file_path" )
        row = layout.row()
        row.prop(scn, "lookdev_actor_import_file_path" )
        
        layout.row().separator(factor=3)
        col = layout.column(align=True)
        col.operator("vse.lookdev_load", text="Load LookDev blend", icon="TIME")
        col = layout.column(align=True)
        col.operator("vse.lookdev_setup", text="Import and Setup Actor", icon="TIME")
        row = layout.row()
        row.label(text = "Ensure the LookDev blend file is loaded before importing/setting up actor", icon = 'INFO')
        row = layout.row()
        row.label(text = "Do not save the LookDev blend file unless you intend on modifying its setup", icon = 'INFO')

        layout.separator()

# Blender Validation
def register():
    bpy.utils.register_class(Render_Tool_Panel)
    bpy.utils.register_class(LookDev_Setup)
    bpy.utils.register_class(LookDev_Load)
    
def unregister():
    bpy.utils.unregister_class(Render_Tool_Panel)
    bpy.utils.unregister_class(LookDev_Setup)
    bpy.utils.unregister_class(LookDev_Load)
    
def assign_control_variables():
    
    bpy.types.Scene.lookdev_blend_file_path  = ( 
        bpy.props.StringProperty(
            name = "VSE LookDev blend file path",
            description = "The correct turntable lookdev blend file path",
            subtype = "FILE_PATH",
            update = validate_blend_Path,
            default = "N:\\Cricket\\assets\\LookDevBlend\\VSE_LookDev_Turntable.blend"))
    
    bpy.types.Scene.lookdev_actor_import_file_path  = ( 
        bpy.props.StringProperty(
            name = "FBX Path",
            description = "FBX Import File Path",
            subtype = "FILE_PATH",
            update = validate_fbx_Path,
            default = "N:\\Cricket\\assets\\Mesh_Skeleton\\LookDevTest.fbx"))
            
def validate_blend_Path(self, context):
    blend_file_path = bpy.context.scene.lookdev_blend_file_path
    if (blend_file_path[-5:] != "blend" and blend_file_path != " "):
        ShowMessageBox("Please select correct turntable blend file", "File not Blend!", 'ERROR')
        bpy.context.scene.lookdev_blend_file_path = " "# To avoid recursion error, use double empty
        return    
        
def validate_fbx_Path(self, context):
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
