import bpy

from VSE_Rendering import VSERender_Engine

class Load_Render_Ready_Blender(bpy.types.Operator):
    """Loads the default render ready blend scene"""
    bl_idname = "vse.render_load"
    bl_label = "VSE Render blend loadOperator"
    
    _render_ready_blend_path = None
    
    def execute(self, context):

        print("\n=====================================================================================")
        print("VSE Render Automation\n")  

        self._render_ready_blend_path = bpy.context.scene.vse_render_blend_path 
        self._load_blend()

        return {"FINISHED"}
    
    def _load_blend(self):
        print("\nLoading render ready blend file")
        bpy.ops.wm.open_mainfile(filepath=self._render_ready_blend_path)
        print("Success")

class Render_And_Composite(bpy.types.Operator):
    """Renders 3 compulsory EXRs (Back, Actors, UVs), composites them with CompVV, and then sequences those images with MakeVV to the specified path"""
    bl_idname = "vse.render"
    bl_label = "VSE Render Operator"
    
    def execute(self, context):

        _rendering_engine = VSERender_Engine.Rendering_Engine(bpy.context.scene.vse_exr_output_path,
                                                            bpy.context.scene.vse_png_output_path,
                                                            bpy.context.scene.vse_vision_video_output_path,
                                                            bpy.context.scene.vse_frame_start,
                                                            bpy.context.scene.vse_frame_end,
                                                            bpy.context.scene.vse_frame_rate,
                                                            bpy.context.scene.vse_max_render_samples,
                                                            bpy.context.scene.vse_exr_render,    
                                                            bpy.context.scene.vse_exr_back,
                                                            bpy.context.scene.vse_exr_actors,
                                                            bpy.context.scene.vse_exr_uvs,
                                                            bpy.context.scene.vse_composite,
                                                            bpy.context.scene.vse_make_vv)
        _rendering_engine.render_and_composite()

        return {"FINISHED"}
                     
    
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
# therefore calling register from the script is unecessary unless the is manually run through Blender
if __name__ == "__main__":
    register()
    
assign_control_variables()
