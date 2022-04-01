import bpy
from bpy.types import (
    #Action,
    Context,
    #Event,
    #FileSelectEntry,
    #Object,
    Operator)
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty)

from typing import Set

from . import animation_creation

def start_frame_read (self):
    return bpy.context.window_manager.animlib_frame_range[0]

def end_frame_read (self):
    return bpy.context.window_manager.animlib_frame_range[1]

#def start_frame_set (self, value):
    #self.first_read = True
    #self["first_read"] = value

#def start_frame_set_update(self, context):
    #self.first_read = True

class ANIMLIB_OT_create_animation_asset(Operator):
    bl_idname = "animlib.create_animation_asset" 
    bl_label = "Create Animation Asset"
    bl_description = (
        "Create a new Action that contains the specified keyframe range of the selected object, and mark it as Asset. "
        "The asset will be stored in the current blend file"
    )
    # Register required for redo window 
    bl_options = {"REGISTER", "UNDO"}

    #first_read: BoolProperty(default = False, options = {"HIDDEN", "LIBRARY_EDITABLE", "SKIP_SAVE", "TEXTEDIT_UPDATE"})
    animation_name: StringProperty(name="Animation Name")  # type: ignore

    start_frame: IntProperty(name="Start Frame", get=start_frame_read) # Martin to do: see if you can use exposed start and end frame options to this default
    end_frame: IntProperty(name="End Frame", get=end_frame_read)

    def execute(self, context: Context) -> Set[str]:

        animation_name = self.animation_name or "Animation_" + context.object.name
        start_frame = self.start_frame or context.window_manager.animlib_frame_range[0]
        end_frame = self.end_frame or context.window_manager.animlib_frame_range[1]

        animation_asset = animation_creation.create_animation_asset(
            context,
            animation_name,
            start_frame,
            end_frame)

        return {'FINISHED'}

classes = (
    ANIMLIB_OT_create_animation_asset,)

# Convenient utils method that loops through the list of classes and un/registers them accordingly
_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)

def register() -> None:

    _register_classes()

def unregister() -> None:

    _unregister_classes()
