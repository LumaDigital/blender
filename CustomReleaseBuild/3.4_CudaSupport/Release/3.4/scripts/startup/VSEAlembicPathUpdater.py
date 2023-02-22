import bpy
import os

class Update_Actors_Alembic_References(bpy.types.Operator):
    """Updates all object mesh sequence modifiers to the desired base directory"""
    bl_idname = "vse.update_alembic_references"
    bl_label = "Update Alembic references"

    Mesh_Sequence_Modifier_Name = "MeshSequenceCache"
    Alembic_Base_Directory_Name = "alembic"

    def execute(self, context):

        print("\n============================================================================================================VSE Alembic reference updater")
        self.UpdateCollectionObjectsReferences(bpy.context.scene.vse_first_collection_name)
        self.UpdateCollectionObjectsReferences(bpy.context.scene.vse_second_collection_name)
        print("\n============================================================================================================VSE Alembic reference updater")
        return {'FINISHED'}

    def UpdateCollectionObjectsReferences(self, collection_name):

        if (collection_name in bpy.data.collections):
            current_prefix = " "
            for collection_object in bpy.data.collections[collection_name].all_objects:
                if current_prefix in collection_object.name:
                    continue

                if (self.Mesh_Sequence_Modifier_Name not in collection_object.modifiers):
                    print("\nVSE WARNING:\nThere is no mesh sequence modifier on this object: " + collection_object.name + "\nSkipping.")
                    continue

                object_modifier = collection_object.modifiers[self.Mesh_Sequence_Modifier_Name]

                if hasattr(object_modifier.cache_file, "filepath") == False:
                    print("\nVSE WARNING:\nThere is no alembic cache on this object: " + collection_object.name + "\nSkipping.")
                    continue

                object_cache_file = object_modifier.cache_file

                current_prefix = collection_object.name.split("_")[0]
                print("\n\nCurrent Object:     " + current_prefix)
                print("ABC Path:        " + object_cache_file.filepath)

                path_start_index = object_cache_file.filepath.lower().find(self.Alembic_Base_Directory_Name) + len(self.Alembic_Base_Directory_Name)
                print("New Base Alembic Path: " + bpy.context.scene.vse_new_alembic_base_directory)
                print("Split Path: " + object_cache_file.filepath[path_start_index:])

                new_path = bpy.context.scene.vse_new_alembic_base_directory + object_cache_file.filepath[path_start_index:]
                object_cache_file.filepath = new_path
                print("New path:   "  + new_path)
        else:
            print("\nVSE WARNING:\nCollection Missing: " + collection_name + "\nSkipping.")

class Alembic_Path_Update_Tool_Panel(bpy.types.Panel):
    bl_label = "VSE Alembic Path Update tool"
    bl_idname = "LD_PT_AlembicPathUpdateTool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VSE Alembics'

    def draw(self, context):

        layout = self.layout
        scn = bpy.context.scene

        layout.row().separator()
        row = layout.row()
        row.label(text = "Name of directory to replace")
        row = layout.row()
        row.prop(scn, "vse_directory_name_start")

        row = layout.row()
        row.label(text = "First Collection Name")
        row = layout.row()
        row.prop(scn, "vse_first_collection_name")

        row = layout.row()
        row.label(text = "Second Collection Name")
        row = layout.row()
        row.prop(scn, "vse_second_collection_name")

        row = layout.row()
        row.label(text = "New Alembic base directory:")
        row = layout.row()
        row.prop(scn, "vse_new_alembic_base_directory")

        layout.separator()
        col = layout.column(align=True)
        col.operator("vse.update_alembic_references", text = "Update Alembic References", icon = "TIME")
        layout.separator()

def assign_control_variables():

    bpy.types.Scene.vse_directory_name_start = bpy.props.StringProperty(
        name = "",
        default = "alembic",
        description = "The name of the cache reference directory (lower case) you want to replace with the 'New Alembic base directory'")

    bpy.types.Scene.vse_new_alembic_base_directory = bpy.props.StringProperty(
        name = "",
        subtype = "DIR_PATH",
        description = "The cache reference alembic directory is replaced with this new directory path")

    bpy.types.Scene.vse_first_collection_name = bpy.props.StringProperty(
        name = "",
        default = "TeamA",
        description = "The first collection of objects to have its cache references updated")

    bpy.types.Scene.vse_second_collection_name = bpy.props.StringProperty(
        name = "",
        default = "TeamB",
        description = "The second collection of objects to have its cache references updated")

assign_control_variables()

# Blender Validation
def register():
    bpy.utils.register_class(Alembic_Path_Update_Tool_Panel)
    bpy.utils.register_class(Update_Actors_Alembic_References)
    
def unregister():
    bpy.utils.unregister_class(Alembic_Path_Update_Tool_Panel)
    bpy.utils.unregister_class(Update_Actors_Alembic_References)
