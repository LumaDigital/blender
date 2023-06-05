import bpy
import os

Output_file_extension = ".mp4"

class Rename_Capture_Output(bpy.types.Operator):
    """Updates the capture output to the desired directory"""
    bl_idname = "vse.rename_capture_output_directory"
    bl_label = "Rename Capture Output"

    def execute(self, context):
        self.UpdateCaptureOutput()

        return {'FINISHED'}

    def UpdateCaptureOutput(self):
        scene_name =  bpy.path.basename(bpy.context.blend_data.filepath)
        output_name = "\\" + os.path.basename(scene_name).split(".")[0] + Output_file_extension

        bpy.context.scene.render.filepath = os.path.realpath(bpy.path.abspath(bpy.context.scene.vse_directory_name)) + output_name
        print("\n==============================================================VSE Capture Output renamed")

        return {'FINISHED'}


class Rename_Capture_Output_Panel(bpy.types.Panel):
    bl_label = "VSE Capture Output Rename tool"
    bl_idname = "LD_PT_CaptureOutputRenameTool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VSE Capture Output'

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        row = layout.row()
        row.label(text = "Base directory for Capture")
        row = layout.row()
        row.prop(scn, "vse_directory_name")

        col = layout.column(align = True)
        col.operator("vse.rename_capture_output_directory", text = "Update Capture Output", icon = "TIME")
        layout.separator()

def assign_control_variables():
    bpy.types.Scene.vse_directory_name = bpy.props.StringProperty(
        name = "",
        subtype = "DIR_PATH",
        description = "The Output directory for the capture that needs to be changed")

assign_control_variables()

# Blender Validation
def register():
    bpy.utils.register_class(Rename_Capture_Output_Panel)
    bpy.utils.register_class(Rename_Capture_Output)
    
def unregister():
    bpy.utils.unregister_class(Rename_Capture_Output_Panel)
    bpy.utils.unregister_class(Rename_Capture_Output)
