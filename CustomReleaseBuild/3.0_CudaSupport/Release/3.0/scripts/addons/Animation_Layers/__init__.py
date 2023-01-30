# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


bl_info = {
    "name": "Animation Layers",
    "author": "Tal Hershkovich",
    "version" : (2, 0, 1, 3),
    "blender" : (2, 92, 0),
    "location": "View3D - Properties - Animation Panel",
    "description": "Simplifying the NLA editor into an animation layers UI and workflow",
    "warning": "",
    "wiki_url": "",
    "category": "Animation"}


if "bpy" in locals():
    import importlib
    if "bake_ops" in locals():
        importlib.reload(bake_ops)
    if "anim_layers" in locals():
        importlib.reload(anim_layers)
    if "anim_layers" in locals():
        importlib.reload(subscriptions)
    if "addon_updater_ops" in locals():
        importlib.reload(addon_updater_ops)

import bpy
from . import addon_updater_ops
from . import anim_layers
from . import bake_ops
from . import subscriptions

class AnimLayersSettings(bpy.types.PropertyGroup):

    turn_on: bpy.props.BoolProperty(name="Turn Animation Layers On", description="Turn on and start Animation Layers", default=False, options={'HIDDEN'}, update = anim_layers.turn_animlayers_on, override = {'LIBRARY_OVERRIDABLE'})
    layer_index: bpy.props.IntProperty(update = anim_layers.update_layer_index, options={'LIBRARY_EDITABLE'}, default = 0, override = {'LIBRARY_OVERRIDABLE'})
    linked: bpy.props.BoolProperty(name="Linked", description="Duplicate a layer with a linked action", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    smartbake: bpy.props.BoolProperty(name="Smart Bake", description="Stay with the same amount of keyframes after merging and baking", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    onlyselected: bpy.props.BoolProperty(name="Only selected Bones", description="Bake only selected Armature controls", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    clearconstraints: bpy.props.BoolProperty(name="Clear constraints", description="Clear constraints during bake", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    mergefcurves: bpy.props.BoolProperty(name="Merge Cyclic & Fcurve modifiers", description="Include Fcurve modifiers in the bake", default = True, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    view_all_keyframes: bpy.props.BoolProperty(name="View", description="View keyframes from multiple layers, use lock and mute to exclude layers", default=False, update = anim_layers.view_all_keyframes, override = {'LIBRARY_OVERRIDABLE'})
    edit_all_keyframes: bpy.props.BoolProperty(name="Edit", description="Edit keyframes from multiple layers", default=False, update = anim_layers.unlock_edit_keyframes, override = {'LIBRARY_OVERRIDABLE'})
    only_selected_bones: bpy.props.BoolProperty(name="Only Selected Bones", description="Edit and view only selected bones", default=False, update = anim_layers.only_selected_bones, override = {'LIBRARY_OVERRIDABLE'})
    view_all_type: bpy.props.EnumProperty(name="Type", description="Select visibiltiy type of keyframes", update = anim_layers.view_all_keyframes, override = {'LIBRARY_OVERRIDABLE'},
        items = [
            ('BREAKDOWN', 'Breakdown', 'select Breakdown visibility'),
            ('JITTER', 'Jitter', 'select Jitter visibility'),
            ('MOVING_HOLD', 'Moving Hold', 'select Moving Hold visibility'),
            ('EXTREME', 'Extreme', 'select Extreme visibility'),
            ('KEYFRAME', 'Keyframe', 'select Keyframe visibility')
        ]
    )
    baketype : bpy.props.EnumProperty(name = '', description="Type of Bake", items = [('AL', 'Anim Layers','Use Animation Layers Bake',0), ('BLENDER', 'Blender Bake', 'Use Blender internal Bake',1)], override = {'LIBRARY_OVERRIDABLE'})
    direction: bpy.props.EnumProperty(name = '', description="Select direction of merge", items = [('UP', 'Up','Merge upwards','TRIA_UP',1), ('DOWN', 'Down', 'Merge downwards','TRIA_DOWN',0), ('ALL', 'All', 'Merge all layers')], override = {'LIBRARY_OVERRIDABLE'})
    operator : bpy.props.EnumProperty(name = '', description="Type of bake", items = [('NEW', 'New Baked Layer','Bake into a New Layer','NLA',1), ('MERGE', 'Merge', 'Merge Layers','NLA_PUSHDOWN',0)], override = {'LIBRARY_OVERRIDABLE'})
    blend_type :  bpy.props.EnumProperty(name = 'Blend Type', description="Blend Type", 
        items = [('REPLACE', 'Replace', 'Use as a Base Layer'), ('ADD', 'Add', 'Use as an Additive Layer'), ('SUBTRACT', 'Subtract', 'Use as an Subtract Layer')], update = anim_layers.blend_type_update , override = {'LIBRARY_OVERRIDABLE'})
    data_type :  bpy.props.EnumProperty(name = 'Data Type', description="Select type of action data", default = 'OBJECT', update = anim_layers.data_type_update,
        items = [('KEY', 'Shapekey', 'Switch to shapekey animation layers'), ('OBJECT', 'Object', 'Switch to object animation')], override = {'LIBRARY_OVERRIDABLE'})#, update = anim_layers.blend_type_update
    auto_rename: bpy.props.BoolProperty(name="Auto Rename Layer", description="Rename layer to match to selected action", default=True, update = anim_layers.auto_rename, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    auto_blend: bpy.props.BoolProperty(name="Auto Blend", description="Apply blend type automatically based on scale and rotation values", default=True, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'})
    fcurves: bpy.props.IntProperty(name='fcurves', description='helper to check if fcurves are changed', default=0, override = {'LIBRARY_OVERRIDABLE'})

class AnimLayersItems(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="AnimLayer", override = {'LIBRARY_OVERRIDABLE'}, update = anim_layers.layer_name_update)
    mute: bpy.props.BoolProperty(name="Mute", description="Mute Animation Layer", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'}, update = anim_layers.layer_mute)
    lock: bpy.props.BoolProperty(name="Lock", description="Lock Animation Layer", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'}, update = anim_layers.layer_lock)
    solo: bpy.props.BoolProperty(name="Solo", description="Solo Animation Layer", default=False, options={'HIDDEN'}, override = {'LIBRARY_OVERRIDABLE'}, update = anim_layers.layer_solo)
    influence: bpy.props.FloatProperty(name="Layer Influence", description="Layer Influence", min = 0.0, options={'ANIMATABLE'}, max = 1.0, default = 1.0, precision = 3, update = anim_layers.influence_update, override = {'LIBRARY_OVERRIDABLE'})
    influence_mute: bpy.props.BoolProperty(name="Animated Influence", description="Turn Animated influence On/Off", default=False, options={'HIDDEN'}, update = anim_layers.influence_mute_update, override = {'LIBRARY_OVERRIDABLE'})
    action: bpy.props.EnumProperty(name = 'Actions', description = "Select action", update = anim_layers.load_action, items =  anim_layers.action_items, override = {'LIBRARY_OVERRIDABLE'})
    

class AnimLayersObjects(bpy.types.PropertyGroup):

    object: bpy.props.PointerProperty(name = "object", description = "objects with animation layers turned on", type=bpy.types.Object, override = {'LIBRARY_OVERRIDABLE'})


# Add-ons Preferences Update Panel
# Define Panel classes for updating
panels = (anim_layers.ANIMLAYERS_PT_Panel,)

def update_panel(self, context):
    message = "AnimationLayers: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            print (panel.bl_category)
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass
    
@addon_updater_ops.make_annotations
class AnimLayersAddonPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    category: bpy.props.StringProperty(
        name="Tab Category",
        description="Choose a name for the category of the panel",
        default="Animation",
        update=update_panel
    )
    
    # addon updater preferences from `__init__`, be sure to copy all of them
    auto_check_update: bpy.props.BoolProperty(
        name = "Auto-check for Update",
        description = "If enabled, auto-check for updates using an interval",
        default = False,
    )

    updater_interval_months: bpy.props.IntProperty(
        name='Months',
        description = "Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_interval_days: bpy.props.IntProperty(
        name='Days',
        description = "Number of days between checking for updates",
        default=7,
        min=0,
    
    )
    updater_interval_hours: bpy.props.IntProperty(
        name='Hours',
        description = "Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_interval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description = "Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        layout = self.layout
        addon_updater_ops.update_settings_ui(self, context)
        
        row = layout.row()
        col = row.column()

        col.label(text="Tab Category:")
        col.prop(self, "category", text="")

classes = (AnimLayersAddonPreferences, AnimLayersSettings, AnimLayersItems, AnimLayersObjects)

def register():
    addon_updater_ops.register(bl_info)
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
  
    bake_ops.register()
    anim_layers.register()
    #bpy.utils.register_class(AnimLayersAddonPreferences)
    addon_updater_ops.make_annotations(AnimLayersAddonPreferences) # to avoid blender 2.8 warnings
    #Overridable items
    bpy.types.Object.als = bpy.props.PointerProperty(type = AnimLayersSettings, options={'LIBRARY_EDITABLE'}, override = {'LIBRARY_OVERRIDABLE'})
    bpy.types.Object.Anim_Layers = bpy.props.CollectionProperty(type = AnimLayersItems, override = {'LIBRARY_OVERRIDABLE', 'USE_INSERTION'})
    bpy.types.Scene.AL_objects = bpy.props.CollectionProperty(type = AnimLayersObjects, options={'LIBRARY_EDITABLE'}, override = {'LIBRARY_OVERRIDABLE', 'USE_INSERTION'})

def unregister():
    addon_updater_ops.unregister()
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    bake_ops.unregister()
    anim_layers.unregister()
    #del bpy.types.Object.track_list_index
    del bpy.types.Object.als
    del bpy.types.Object.Anim_Layers
    del bpy.types.Scene.AL_objects


if __name__ == "__main__":
    register()