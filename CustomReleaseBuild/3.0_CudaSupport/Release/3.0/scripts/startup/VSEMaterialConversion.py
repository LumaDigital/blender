import bpy
from bpy.props import EnumProperty

TEXTURE_SUBSTRING = "Image Texture"
NO_TEXTURE_WARNING_MESSAGE = "Material textures not found" 

class Change_Textures_Colour_Mode(bpy.types.Operator):
    """Changes the texture nodes' colour mode of all materials to the selected option"""
    bl_idname = "vse.change_textures_colour_mode"
    bl_label = "VSE Material textures colour mode converter"

    def execute(self, context):

        colour_mode_name = bpy.context.scene.vse_material_conversion_colour_mode
        for material in bpy.data.materials:
            node_tree = material.node_tree
            if node_tree != None:
                for node in node_tree.nodes:
                    if TEXTURE_SUBSTRING in node.name:
                        node.image.colorspace_settings.name = colour_mode_name

        return {"FINISHED"}

class Change_Material_Texture(bpy.types.Operator):
    """Changes the selected texture node to an image of your choosing"""
    bl_idname = "vse.change_material_texture"
    bl_label = "Switch Texture"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        material_name = bpy.context.scene.vse_material_with_textures
        texture_name = bpy.context.scene.vse_materials_texture

        for node in bpy.data.materials[material_name].node_tree.nodes:
            if TEXTURE_SUBSTRING in node.name and texture_name in node.image.name:
                node.image = bpy.data.images.load(self.filepath)
                break

        return {'FINISHED'}

class Material_Conversion_Tool_Panel(bpy.types.Panel):
    bl_label = "VSE Material Conversion Tool"
    bl_idname = "LD_PT_MaterialConversionPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VSE Materials'

    def draw(self, context):

        layout = self.layout
        scn = bpy.context.scene
       
        layout.row().separator(factor=2)
        row = layout.row()
        row.prop(scn, "vse_material_conversion_change_image")
        if bpy.context.scene.vse_material_conversion_change_image:

            row = layout.row()
            if blend_has_textures():
                row.prop(scn, "vse_material_with_textures")
                row = layout.row()
                row.prop(scn, "vse_materials_texture")
                col = layout.column(align=True)
                col.operator("vse.change_material_texture", text="Change selected material texture", icon="TIME")
            else:
                row.label(text = NO_TEXTURE_WARNING_MESSAGE)


        row = layout.row()
        row.prop(scn, "vse_material_conversion_change_colour_mode")

        if bpy.context.scene.vse_material_conversion_change_colour_mode:
            row = layout.row()
            if blend_has_textures():
                row.prop(scn, "vse_material_conversion_colour_mode")
                col = layout.column(align=True)
                col.operator("vse.change_textures_colour_mode", text="Change all textures' Colour mode", icon="TIME")
            else:
                row.label(text = NO_TEXTURE_WARNING_MESSAGE)

        layout.separator()

def blend_has_textures():
    for material in bpy.data.materials:
        node_tree = material.node_tree
        if node_tree != None:
            for node in node_tree.nodes:
                if TEXTURE_SUBSTRING in node.name:
                    return True

    return False

def get_all_materials_with_textures(self, context):
    materials_with_textures = []

    for material in bpy.data.materials:
        node_tree = material.node_tree
        if node_tree != None:
            for node in node_tree.nodes:
                if TEXTURE_SUBSTRING in node.name:
                    materials_with_textures.append((material.name, material.name, material.name))
                    break

    return materials_with_textures

def get_all_materials_textures(self, context):

    materials_textures = []
    selected_material = bpy.data.materials[bpy.context.scene.vse_material_with_textures]
    for node in selected_material.node_tree.nodes:
        if TEXTURE_SUBSTRING in node.name:
            materials_textures.append((node.image.name, node.image.name, node.image.name))

    return materials_textures

def assign_control_variables():
    bpy.types.Scene.vse_material_conversion_change_image  = ( 
        bpy.props.BoolProperty(name = "Change materials' textures", description="If set to true, you will be asked what new image you'd like for each material", default=False))

    bpy.types.Scene.vse_material_conversion_change_colour_mode  = ( 
        bpy.props.BoolProperty(name = "Change textures' colour mode", default=False))

    # TODO: Find the list of available colour modes instead of hardcoding them
    colour_modes = [('sRGB', 'sRGB', ''),
                   ('ACES - ACES2065-1', 'ACES - ACES2065-1', ''),
                   ('ACES - ACEScc', 'ACES - ACEScc', ''),
                   ('ACES - ACEScct', 'ACES - ACEScct', ''),
                   ('ACES - ACEScg', 'ACES - ACEScg', ''),
                   ('Output - sRGB', 'Output - sRGB', ''),
                   ('Utility - Linear - sRGB', 'Utility - Linear - sRGB', ''),
                   ('Utility - sRGB - Texture', 'Utility - sRGB - Texture', ''),
                   ('Linear', 'Linear', ''),
                   ('Raw', 'Raw', ''),
                   ('Linear ACES', 'Linear ACES', ''),
                   ('nuke_rec709', 'nuke_rec709', ''),
                   ('XYZ', 'XYZ', ''),
                   ('lg10', 'lg10', ''),
                   ('Non-Color', 'Non-Color', ''),
                   ('Filmic Log', 'Filmic Log', ''),
                   ('Filmic sRGB', 'Filmic sRGB', ''),
                   ('False Color', 'False Color', ''),]

    bpy.types.Scene.vse_material_conversion_colour_mode  = ( 
        bpy.props.EnumProperty(items = colour_modes, name = "Colour mode"))

    bpy.types.Scene.vse_material_with_textures = bpy.props.EnumProperty(items = get_all_materials_with_textures, name = "Material")

    bpy.types.Scene.vse_materials_texture = bpy.props.EnumProperty(items = get_all_materials_textures, name = "Texture")

assign_control_variables()

# Blender Validation
def register():
    bpy.utils.register_class(Material_Conversion_Tool_Panel)
    bpy.utils.register_class(Change_Textures_Colour_Mode)
    bpy.utils.register_class(Change_Material_Texture)
    
def unregister():
    bpy.utils.unregister_class(Material_Conversion_Tool_Panel)
    bpy.utils.unregister_class(Change_Textures_Colour_Mode)
    bpy.utils.unregister_class(Change_Material_Texture)
