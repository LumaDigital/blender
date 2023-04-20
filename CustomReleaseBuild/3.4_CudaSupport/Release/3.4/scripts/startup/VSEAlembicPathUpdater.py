import bpy
import os

# Ideally we would like to loop through each object's modifiers however I was unable to get it to work so the modifiers that need to be changed have their names hardcoded below 
Mesh_Sequence_Modifier_Name = "MeshSequenceCache"
Alternate_Modifier_Name = "Generated Modifier"

class Update_Actors_Alembic_References(bpy.types.Operator):
    """Updates all object mesh sequence modifiers to the desired base directory"""
    bl_idname = "vse.update_alembic_references"
    bl_label = "Update Alembic references"

    def execute(self, context):

        print("\n============================================================================================================VSE Alembic reference updater starting")
        self.UpdateCollectionObjectsReferences()
        print("\n============================================================================================================VSE Alembic reference updater complete\n")
        return {'FINISHED'}

    def UpdateCollectionObjectsReferences(self):

        absolute_filepath_to_replace = os.path.realpath(bpy.path.abspath(bpy.context.scene.vse_directory_name_start))
        print("\nOLD Base Alembic Path: " + absolute_filepath_to_replace)

        absolute_new_filepath = os.path.realpath(bpy.path.abspath(bpy.context.scene.vse_new_alembic_base_directory))
        print("\nNEW Base Alembic Path: " + absolute_new_filepath)

        for collection in bpy.data.collections:
                for collection_object in collection.all_objects:

                    if (Mesh_Sequence_Modifier_Name not in collection_object.modifiers):
                        print("\nVSE WARNING:\nThere is no '" + Mesh_Sequence_Modifier_Name + "' modifier on this object: " + collection_object.name + "\nSkipping.")
                        continue

                    # Set reference to MeshSequenceCache cache file and convert filepath to absolute
                    object_modifier_cache_file = collection_object.modifiers[Mesh_Sequence_Modifier_Name].cache_file
                    absolute_modifier_filepath = os.path.realpath(bpy.path.abspath(object_modifier_cache_file.filepath))

                    if (absolute_filepath_to_replace in absolute_modifier_filepath):

                        # Perform string replacement to new Alembic filepath and replace the old reference
                        object_modifier_cache_file.filepath = os.path.realpath(bpy.path.abspath(object_modifier_cache_file.filepath.replace(absolute_filepath_to_replace, absolute_new_filepath)))
                        
                        print("\n\nCurrent Object:      " + collection_object.name)
                        print(Mesh_Sequence_Modifier_Name + " - New Base Alembic Path:\n" + object_modifier_cache_file.filepath)
                    else:
                        print("\nVSE WARNING:\n" + collection_object.name + " alembic reference in cache '" + Mesh_Sequence_Modifier_Name + "' points to a different directory!")

                    if (Alternate_Modifier_Name not in collection_object.modifiers):
                        print("\nVSE WARNING:\nThere is no '" + Alternate_Modifier_Name + "' modifier on this object: " + collection_object.name + "\nSkipping.")
                        continue

                    # Set reference to Generated Modifier cache file and convert filepath to absolute
                    object_modifier_cache_file = collection_object.modifiers[Alternate_Modifier_Name].cache_file
                    absolute_modifier_filepath = os.path.realpath(bpy.path.abspath(object_modifier_cache_file.filepath))

                    if (absolute_filepath_to_replace in absolute_modifier_filepath):

                        object_modifier_cache_file.filepath = os.path.realpath(bpy.path.abspath(object_modifier_cache_file.filepath.replace(absolute_filepath_to_replace, absolute_new_filepath)))

                        print(Alternate_Modifier_Name + " - New Base Alembic Path:\n" + object_modifier_cache_file.filepath)
                    else:
                        print("\nVSE WARNING:\n" + collection_object.name + " alembic reference in cache '" + Alternate_Modifier_Name + "' points to a different directory!")


class Generate_Alembic_Reference_Textfile(bpy.types.Operator):
    """Generates textfile highlighting Alembics in the scene to the blend file's base directory"""
    bl_idname = "vse.generate_alembic_reference_textfile"
    bl_label = "Generate Alembic reference textfile"

    def execute(self, context):

        print("\n============================================================================================================VSE Alembic reference textfile generating")
        self.GenerateAlembicReferenceTextfile()
        print("\n============================================================================================================VSE Alembic reference textfile generated\n")
        return {'FINISHED'}

    def GenerateAlembicReferenceTextfile(self):
        
        Alembic_Textfile=open(bpy.data.filepath + "_Alembics.txt", 'w')

        for collection in bpy.data.collections:
            for collection_object in collection.all_objects:

                if (Mesh_Sequence_Modifier_Name not in collection_object.modifiers):
                    print("\nVSE WARNING:\nThere is no '" + Mesh_Sequence_Modifier_Name + "' modifier on this object: " + collection_object.name + "\nSkipping.")
                    continue

                print("\n" + collection_object.name + ":\n'" + Mesh_Sequence_Modifier_Name + "' modifier found, writing to textfile.")

                object_modifier_cache_file = collection_object.modifiers[Mesh_Sequence_Modifier_Name].cache_file
                absolute_modifier_filepath = os.path.realpath(bpy.path.abspath(object_modifier_cache_file.filepath))

                Alembic_Textfile.write("\n\nCollection: " + collection.name + "\nObject in Collection: " + collection_object.name + "\n" + Mesh_Sequence_Modifier_Name + " Alembic path: " + absolute_modifier_filepath)

                if (Alternate_Modifier_Name not in collection_object.modifiers):
                    print("\nVSE WARNING:\nThere is no '" + Alternate_Modifier_Name + "' modifier on this object: " + collection_object.name + "\nSkipping.")
                    continue

                print("\n" + collection_object.name + ":\n'" + Alternate_Modifier_Name + "' modifier found, writing to textfile.")

                object_modifier_cache_file = collection_object.modifiers[Alternate_Modifier_Name].cache_file
                absolute_modifier_filepath = os.path.realpath(bpy.path.abspath(object_modifier_cache_file.filepath))

                Alembic_Textfile.write("\n" + Alternate_Modifier_Name + " Alembic path: " + absolute_modifier_filepath)

        Alembic_Textfile.close()


class Alembic_Path_Update_Tool_Panel(bpy.types.Panel):
    bl_label = "VSE Alembic Path Update tool"
    bl_idname = "LD_PT_AlembicPathUpdateTool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VSE Alembics'

    def draw(self, context):

        layout = self.layout
        scn = bpy.context.scene

        row = layout.row()
        row.label(text = "Base directory to replace")
        row = layout.row()
        row.prop(scn, "vse_directory_name_start")

        row = layout.row()
        row.label(text = "New Alembic base directory:")
        row = layout.row()
        row.prop(scn, "vse_new_alembic_base_directory")

        col = layout.column(align=True)
        col.operator("vse.update_alembic_references", text = "Update Alembic References", icon = "TIME")
        layout.separator()

        layout.separator()
        col = layout.column(align=True)
        col.operator("vse.generate_alembic_reference_textfile", text = "Generate Alembic Reference Textfile", icon = "TIME")

def assign_control_variables():

    bpy.types.Scene.vse_directory_name_start = bpy.props.StringProperty(
        name = "",
        subtype = "DIR_PATH",
        description = "The original cache reference alembic directory to be replaced")

    bpy.types.Scene.vse_new_alembic_base_directory = bpy.props.StringProperty(
        name = "",
        subtype = "DIR_PATH",
        description = "The cache reference alembic directory is replaced with this new directory path")

assign_control_variables()

# Blender Validation
def register():
    bpy.utils.register_class(Alembic_Path_Update_Tool_Panel)
    bpy.utils.register_class(Update_Actors_Alembic_References)
    bpy.utils.register_class(Generate_Alembic_Reference_Textfile)
    
def unregister():
    bpy.utils.unregister_class(Alembic_Path_Update_Tool_Panel)
    bpy.utils.unregister_class(Update_Actors_Alembic_References)
    bpy.utils.unregister_class(Generate_Alembic_Reference_Textfile)
