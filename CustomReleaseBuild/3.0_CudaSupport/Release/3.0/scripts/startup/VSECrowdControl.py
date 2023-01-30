import bpy

_CROWD_COLLECTION_NAME_SUBSTRING = "All_crowd"

class Handle_Crowd_Objects(bpy.types.Operator):
    """Sets seat object's geometry switch off, and disables seats and stadium in viewport"""
    bl_idname = "vse.crowds"
    bl_label = "VSE Crowd Operator"
    
    _SEATS_COLLECTION_NAME = "Seats"
    _STADIUM_COLLECTION_NAME = "stadium_buildings_COL"
    _CUSTOM_PROPERTY_DRIVER_NAME = "Crowd_on"
    
    def execute(self, context):
        
        bpy.context.scene.vse_crowd_work_state = not bpy.context.scene.vse_crowd_work_state

        for collection in bpy.data.collections:
            if  _CROWD_COLLECTION_NAME_SUBSTRING in collection.name:
                for object in bpy.data.collections[collection.name].all_objects:
                    if (self._SEATS_COLLECTION_NAME in object.name):
                        object.animation_data_clear()

                        # Blender goes against industry standards and uses 0 for True, and 1 for False. To account for this -
                        # all drivers using integer booleans will have their desired values set to the opposite        
                        object[self._CUSTOM_PROPERTY_DRIVER_NAME] = 0
                        object.update_tag()
                        object.select_set(True)
                        
        bpy.data.collections[self._SEATS_COLLECTION_NAME].hide_viewport = bpy.context.scene.vse_crowd_work_state
        bpy.data.collections[self._STADIUM_COLLECTION_NAME].hide_viewport = bpy.context.scene.vse_crowd_work_state
                        
        return {"FINISHED"}

class Show_Crowd_Panel(bpy.types.Panel):
    bl_label = "VSE Crowd Tool"
    bl_idname = "LD_PT_Crowd"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'VSE Crowd'
    
    @classmethod
    def poll(self, context):
        return context.collection != None and _CROWD_COLLECTION_NAME_SUBSTRING in context.collection.name
    
    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene
        
        col = layout.column(align=True)
        col.operator("vse.crowds", text="Toggle work state", icon="TIME")
        
def register():
    bpy.utils.register_class(Show_Crowd_Panel)
    bpy.utils.register_class(Handle_Crowd_Objects)
    
def unregister():
    bpy.utils.unregister_class(Show_Crowd_Panel)
    bpy.utils.unregister_class(Handle_Crowd_Objects)
    
# Assign scene value
bpy.types.Scene.vse_crowd_work_state = bpy.props.BoolProperty(name = "Work State", default=True)
    
