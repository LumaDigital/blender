import bpy
from bpy.types import (
    #AssetHandle,
    Context,
    Panel,
    #UIList,
    #WindowManager,
    #WorkSpace,
)

class animation_library_panel:
    @classmethod
    def animation_library_panel_poll(cls, context: Context) -> bool:
        return bool(
            len(bpy.context.selected_objects)
            )

    @classmethod
    def poll(cls, context: Context) -> bool:
        return cls.animation_library_panel_poll(context);

class VIEW3D_PT_animation_library(animation_library_panel, Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_label = "Animation Library"

    def draw(self, context: Context) -> None:

        layout = self.layout

        row = layout.row(align = True)
        row.label(text = "Row Label")

        col = layout.column(align = True)
        col.label(text = "Col Label")


classes = (
    VIEW3D_PT_animation_library,
    )

# Convenient utils method that loops through the list of classes and un/registers them accordingly
_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)

def register() -> None:

    _register_classes()

def unregister() -> None:

    _unregister_classes()
