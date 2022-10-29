import bpy
import os
import time

_DEFAULT_ABC_PATH = "N:\\Cricket\\assets\\Blender_Rigs\\lighting_cricket_player.abc"

class Add_ABC_Modifier(bpy.types.Operator):
    """Generates a new Cached MeshSequence modifier to the selected object. If a common prefix is found, this generation
    will apply to all objects with that prefix."""
    bl_idname = "vse.modifier_control"
    bl_label = "VSE Add ABC Modifier"

    def execute(self, context):

        split_object_name_list = context.selected_objects[0].name.split('_')
        if len(split_object_name_list) > 0:
            _selected_object_prefix = split_object_name_list[0]

            for object in context.scene.objects:
                split_object_name_list = object.name.split('_')
                if len(split_object_name_list) > 0 and split_object_name_list[0] == _selected_object_prefix:
                    self.AddNewModifier(object)
        else:
            self.AddNewModifier(context.selected_objects[0])

        return {"FINISHED"}

    def AddNewModifier(self, object):

        if len(object.modifiers) == 1:


            previous_cache_list = bpy.data.cache_files[:]
            bpy.ops.cachefile.open(filepath = bpy.context.scene.vse_abc_path)

            new_cache_file = None
            for i in range(len(bpy.data.cache_files)):
                if i >= len(previous_cache_list) or bpy.data.cache_files[i] != previous_cache_list[i]:
                    new_cache_file = bpy.data.cache_files[i]
                    break

            referenced_modifier = object.modifiers[0]
            new_modifier = object.modifiers.new("Generated Modifier", 'MESH_SEQUENCE_CACHE')

            new_modifier.cache_file = new_cache_file
            new_modifier.object_path = referenced_modifier.object_path
            new_modifier.read_data = referenced_modifier.read_data
        else:
            print("\n||WARNING||\nObject: " + object.name + " is either missing a modifier to reference, " +
                  "or already has more than one modifier. Skipping.\n")

class Add_Modifier_Property_Panel(bpy.types.Panel):
    bl_label = "VSE Modifier Tool"
    bl_idname = "LD_PT_Modifier_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'VSE Modifier'
    
    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0 
    
    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        row = layout.row()
        row.label(text = "Alembic Path")
        row = layout.row()
        row.prop(scn, "vse_abc_path")
        row = layout.row()
        row.label(text = "NOTE: All objects with this prefix will be affected.")

        col = layout.column(align=True)
        col.operator("vse.modifier_control", text="Generate new Modifier", icon="TIME")

def register():
    bpy.utils.register_class(Add_Modifier_Property_Panel)
    bpy.utils.register_class(Add_ABC_Modifier)
    
def unregister():
    bpy.utils.unregister_class(Add_Modifier_Property_Panel)
    bpy.utils.unregister_class(Add_ABC_Modifier)

# Assign scene value
bpy.types.Scene.vse_abc_path = bpy.props.StringProperty(
    name = "",
    description = "The referenced ABC path for the cache file",
    subtype = "FILE_PATH",
    default = _DEFAULT_ABC_PATH)
