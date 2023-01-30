import bpy

from bpy.app.handlers import persistent
from bpy.app import driver_namespace
from . import bake_ops
from . import anim_layers
from sys import getsizeof

def subscriptions_remove():
    if len(bpy.context.scene.AL_objects):
        return
    #clear all handlers and subsciptions
    bpy.msgbus.clear_by_owner(bpy.context.scene)
    if check_handler in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(check_handler)
    global action_name
    if 'action_name' in globals():
        del action_name
    
def subscriptions_add(scene):
    #subscriptions
    bpy.msgbus.clear_by_owner(scene)
    subscribe_to_frame_end(scene)
    subscribe_to_influence(scene)
    subscribe_to_track_name(scene)
    subscribe_to_action_name(scene)
    subscribe_to_blend_type(scene)

    if check_handler not in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.append(check_handler)

def check_handler(self, context):
    '''A main function that performs a series of checks using a handler'''
    scene = bpy.context.scene
    #if there are no objects included in animation layers then return
    if not len(scene.AL_objects):
        return
    
    #check if an action was changed, created or removed within all the objects with animation layers
    for i, AL_item in enumerate(scene.AL_objects):
        obj = AL_item.object          
        if obj not in list(scene.objects) or obj is None:
            scene.AL_objects.remove(i)
            continue
        check_sub_track(obj)
        anim_data = anim_layers.anim_data_type(obj)
        if anim_data is None:
            continue
        if not len(anim_data.nla_tracks):
            continue
        #checking the value for comparison before the intial keyframe is set, because of the scale reseting to 0 bug
        update_action(obj, anim_data)
        check_fcurves(obj)
    
    obj = bpy.context.object
    if obj is None:
        return
    anim_data = anim_layers.anim_data_type(obj)        
    if anim_data is None:
        return
    if not anim_data.use_nla:
        obj.als.turn_on = False
        return
    if not len(obj.Anim_Layers):
        return    

    if obj.select_get() == False or not hasattr(anim_data, 'nla_tracks') or not obj.als.turn_on:
        return
    #check if a keyframe was removed
    if bpy.context.active_operator is not None:
        if bpy.context.active_operator.name in ['Transform', 'Delete Keyframes'] and obj.als.edit_all_keyframes:
            anim_layers.edit_all_keyframes()
    
    #continue if locked
    if obj.Anim_Layers[obj.als.layer_index].lock:
        return

    if obj.als.view_all_keyframes:
        anim_layers.hide_view_all_keyframes(obj, anim_data)
        check_selected_bones(obj)

    nla_tracks = anim_data.nla_tracks
    #check if a new track was added within the NLA
    if len(nla_tracks[:-1]) > len(obj.Anim_Layers):
        anim_layers.visible_layers(obj, nla_tracks)
        return

    #check if a new track was removed within the NLA
    if len(nla_tracks[:-1]) < len(obj.Anim_Layers):   
        check_del_track(nla_tracks, obj)
        anim_layers.visible_layers(obj, nla_tracks)
        return   

    influence_sync(obj, nla_tracks)
    influence_check(nla_tracks[obj.als.layer_index])

def update_action(obj, anim_data):
    '''Check if a different action was selected or added in the action editor and update it into the current layer'''
    if obj is None:
        return
    if anim_data is None:
        return
    if len(anim_data.nla_tracks) <= 1:
        return
    nla_tracks = anim_data.nla_tracks
    if len(nla_tracks[obj.als.layer_index].strips) != 1:
        obj.Anim_Layers[obj.als.layer_index].lock = True
        return
    if obj.Anim_Layers[obj.als.layer_index].lock:
        return
    action = anim_data.action
    strip = nla_tracks[obj.als.layer_index].strips[0]
    if action == strip.action and action == nla_tracks[-1].strips[0].action:
        return
    #update the subtract track strip
    nla_tracks[-1].strips[0].action = action
    #update the layer strip with the current action
    emptyAction = True if strip.action is None else False
        
    strip.action = action
    if action is None:
        obj.als.fcurves = 0
        return
    
    #If it's a newly created Action then skip auto blend and rename
    if emptyAction and action.frame_range[1] - action.frame_range[0] == 1:
        return
    if obj.als.auto_blend:
        strip.blend_type = anim_layers.auto_blendtype(obj, action, strip.blend_type)
    if obj.als.auto_rename:
        name = anim_layers.unique_name([track.name for track in nla_tracks if track != nla_tracks[obj.als.layer_index]], action.name)
        obj.Anim_Layers[obj.als.layer_index].name = name
        nla_tracks[obj.als.layer_index].name = name
        strip.name = name
       
def base_initial_key(obj):
    '''Checks the transformation on the Replace layer and the first keyframe and comparing it to the value before it was added'''
    anim_data = obj.animation_data
    for fcu in anim_data.action.fcurves:
        if '.influence' in fcu.data_path:
            continue
        if len(fcu.keyframe_points) != 1:
            continue  
        transform = fcu.data_path.split('.')[-1]
        #reduce the added the values from the other layers
        added_value = layers_added_value(anim_data.nla_tracks, fcu, blend_type = 'ADD')
        attr_value = find_attr_value(obj, fcu)
        
        #apply the original value to the initial keyframe of the fcurve minus the value of the other layers
        if attr_value != fcu.keyframe_points[0].co[1]:
            fcu.keyframe_points[0].co[1] = attr_value - added_value
        fcu.update()
           
    return {'FINISHED'}
                
def check_fcurves(obj):
    '''checks if there are new fcurves'''
    if obj is None:
        return
    if not len(obj.Anim_Layers) or obj not in bpy.context.selected_objects:
        return
    if obj.als.data_type == 'KEY':
        return
    anim_data = obj.animation_data
    action = anim_data.action
    if action is None or len(anim_data.nla_tracks[obj.als.layer_index].strips) != 1:
        return
    if anim_data.nla_tracks[obj.als.layer_index].strips[0].blend_type != 'REPLACE':
        if not obj.als.fcurves:
            obj.als.fcurves = len(action.fcurves)
        return

    if action:
        if obj.als.fcurves != len(action.fcurves):
            base_initial_key(obj)
        obj.als.fcurves = len(action.fcurves)
        return
    obj.als.fcurves = 0

def check_sub_track(obj):
    anim_datas = anim_layers.anim_datas_append(obj)
    for anim_data in anim_datas:
        if not hasattr(anim_data, 'nla_tracks'):
            continue
        if anim_data.action_blend_type != 'ADD':
            anim_data.action_blend_type = 'ADD' 
        nla_tracks = anim_data.nla_tracks
        if not len(nla_tracks):
            return
        if nla_tracks[-1].name == 'Subtract_Layer' and len(nla_tracks[-1].strips) == 1:
            if nla_tracks[-1].strips[0].blend_type == 'SUBTRACT':
            #if there is only sub_track left, then remove it
                if len(nla_tracks) == 1:
                    obj.Anim_Layers.clear()
                    nla_tracks.remove(nla_tracks[0])
                continue
        #check if the subtract track moved to a different location
        for track in reversed(nla_tracks):
            if track.name == 'Subtract_Layer':
                nla_tracks.remove(track)
                break
        anim_layers.add_substract_layer(nla_tracks, anim_data.action)

#check if a track was deleted outside of animation layers
def check_del_track(nla_tracks, obj):
    '''Check if a layer was deleted outside of animation layers, keep only subtract'''

    if not len(nla_tracks):
        obj.Anim_Layers.clear() 
        return     

    #check if sub_track is still there
    if obj.als.layer_index > len(nla_tracks)-2 and nla_tracks[-1].name == 'Subtract_Layer' and nla_tracks[-1].strips[0].blend_type == 'SUBTRACT':
        obj.als.layer_index = len(nla_tracks)-2
        return

def layers_added_value(nla_tracks, fcu, blend_type = None):

    added_value = 0
    frame = bpy.context.scene.frame_current
    replace = False
    for track in nla_tracks:
        if len(track.strips) != 1 or track.strips[0].action is None or track.mute: # 
            continue
        if track.strips[0].blend_type != blend_type and blend_type != None:
            continue
        fcu_track = track.strips[0].action.fcurves.find(fcu.data_path,  index = fcu.array_index)
        if fcu_track is None:
            continue
        if fcu_track.data_path == fcu.data_path and fcu_track.array_index == fcu.array_index:
            #get the influence value either from the attribute or the fcurve
            if not track.strips[0].fcurves[0].mute and len(track.strips[0].fcurves[0].keyframe_points):
                influence = track.strips[0].fcurves[0].evaluate(frame)
            else:
                influence = track.strips[0].influence
            
            if track.strips[0].blend_type == 'REPLACE':
                #need to find the replace layer value with influence
                if (('rotation_quaternion' in fcu.data_path and not fcu.array_index) or 'scale' in fcu.data_path) and not replace:
                    evaluate = fcu_track.evaluate(frame) * influence + (1 - influence)
                else:
                    evaluate = fcu_track.evaluate(frame)*influence
                replace = True
                added_value = evaluate + added_value*(1-influence)
            else:
                added_value += fcu_track.evaluate(frame)*influence

    return added_value

def find_attr_value(obj, fcu):
    #check if the fcurve is from a bone and not the object and get the value of the property
    transform_types = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']
    transform = fcu.data_path.split('.')[-1]
    if obj.type == 'ARMATURE' and fcu.data_path not in transform_types:
        bone = fcu.data_path.split('"')[1]
        #if the fcurve has transformation then get the original value
        if bone not in obj.pose.bones.keys():
            return 0
        if transform in dir(obj.pose.bones[bone]):
            if transform in transform_types: #if it's a vector transform then get the value with array index
                obj_transform = getattr(obj.pose.bones[bone], transform)
                value = obj_transform[fcu.array_index]
            else: #if it's not a vector transform type then get the value of the property
                value = getattr(obj.pose.bones[bone], transform)
        else: #if it's not a tranformation then check if it's a property in the items of the bone
            prop = fcu.data_path.split('"')[-2]
            for item in obj.pose.bones[bone].items():
                if prop == item[0]:
                    #check if the property is of Blender's IDPropertyArray class
                    if hasattr(item[1], 'to_list'):
                        value = item[1][fcu.array_index]
                    else:
                        value = item[1]
                           
            #check if the attr is from a constraint
            if '.constraints' in fcu.data_path:
                attr = fcu.data_path.split('"].')[-1]
                value = getattr(obj.pose.bones[bone].constraints[prop], attr)
    else:
        if fcu.data_path not in transform_types:
            return 0
        obj_transform = getattr(obj, transform)
        value = obj_transform[fcu.array_index]

    if 'value' not in locals():
        return 0

    return value

def influence_sync(obj, nla_tracks):
    #Tracks that dont have keyframes are locked
    for i, track in enumerate(nla_tracks[:-1]):
        if obj.Anim_Layers[i].lock:
            continue
        if not len(track.strips[0].fcurves):
            continue
        if not len(track.strips[0].fcurves[0].keyframe_points):
            #apply the influence property to the temp property when keyframes are removed (but its still locked)
            if not track.strips[0].fcurves[0].lock:
                obj.Anim_Layers[i].influence = track.strips[0].influence
            track.strips[0].fcurves[0].lock = True
    
    if obj.animation_data is None:
        return
    action = obj.animation_data.action
    if action is None or obj != bpy.context.active_object:
        return
    #if a keyframe was found in the temporary property then add it to the 
    data_path = 'Anim_Layers[' + str(obj.als.layer_index) + '].influence'
    fcu_influence = action.fcurves.find(data_path)
    if fcu_influence is None:
        return
    if not len(fcu_influence.keyframe_points):
        return
    #remove the temporary influence
    action.fcurves.remove(fcu_influence)
    #if the action was created just for the influence because of empty object data type then remove the action
    if action.name == obj.name + 'Action' and not len(obj.animation_data.nla_tracks) and not len(action.fcurves):
        bpy.data.actions.remove(action)
    if obj.Anim_Layers[obj.als.layer_index].influence_mute:
        return
    strip = nla_tracks[obj.als.layer_index].strips[0]
    strip.fcurves[0].lock = False
    strip.keyframe_insert('influence')
    strip.fcurves[0].update()


def influence_check(selected_track):
    '''update influence when a keyframe was added without autokey'''
    #skip the next steps if a strip is missing or tracks were removed from the nla tracks
    if len(selected_track.strips) != 1:# or obj.als.layer_index > len(nla_tracks)-2:
        return

    global influence_keys
    if selected_track.strips[0].fcurves[0].mute or not len(selected_track.strips[0].fcurves[0].keyframe_points) or bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        if 'influence_keys' in globals():
            del influence_keys
        return  #when the fcurve doesnt have keyframes, or when autokey is turned on, then return
    
    #update if the influence keyframes are changed. influence_keys are first added in influence_update_callback
    if 'influence_keys' not in globals():
        return
    if influence_keys != [tuple(key.co) for key in selected_track.strips[0].fcurves[0].keyframe_points]:
         selected_track.strips[0].fcurves[0].update()
         del influence_keys
    

def check_selected_bones(obj):
    '''running in the handler and checking if the selected bones were changed during view multiply layer keyframes'''
    if not obj.als.only_selected_bones:
        return
    global selected_bones
    try: 
        selected_bones
    except NameError:
        selected_bones = bpy.context.selected_pose_bones
        return
    else:
        if selected_bones != bpy.context.selected_pose_bones:
            selected_bones = bpy.context.selected_pose_bones
            obj.als.view_all_keyframes = True    

########################### MSGBUS SUBSCRIPTIONS #############################

#Callback function for Scene frame end
def frameend_update_callback(*args):
    '''End the strips at the end of the scene or scene preview'''
    scene = bpy.context.scene
    if not scene.AL_objects:
        return
    if scene.frame_preview_end > scene.frame_end:
        frame_end = bpy.context.scene.frame_preview_end
    else:
        frame_end = bpy.context.scene.frame_end
    for AL_item in scene.AL_objects:
        obj = AL_item.object
        if obj is None:
            continue
        #anim_data = anim_data_type(obj)
        anim_datas = anim_layers.anim_datas_append(obj)

        for anim_data in anim_datas:
            if anim_data is None:
                continue
            for track in anim_data.nla_tracks:
                if len(track.strips) == 1:
                    track.strips[0].action_frame_end = frame_end
                    track.strips[0].frame_end = frame_end
            
#Subscribe to the scene frame_end
def subscribe_to_frame_end(scene):
    '''subscribe_to_frame_end and frame preview end'''
    
    subscribe_end = scene.path_resolve("frame_end", False)
    subscribe_preview_end = scene.path_resolve("frame_preview_end", False)
    
    bpy.msgbus.subscribe_rna(
        key=subscribe_end,
        # owner of msgbus subcribe (for clearing later)
        owner=scene,
        # Args passed to callback function (tuple)
        args=(scene,),
        # Callback function for property update
        notify=frameend_update_callback,)
        
    bpy.msgbus.subscribe_rna(
        key=subscribe_preview_end,
        owner=scene,
        args=(scene,),
        notify=frameend_update_callback,)
        
    bpy.msgbus.publish_rna(key=subscribe_end)
    bpy.msgbus.publish_rna(key=subscribe_preview_end)
    
def track_update_callback(*args):
    '''update layers with the tracks name'''
    if not bpy.context.selected_objects:
        return
    obj = bpy.context.object
    if obj is None:
        return
    if not obj.als.turn_on:
        return
    current_anim_data = anim_layers.anim_data_type(obj)
    anim_datas = anim_layers.anim_datas_append(obj)
    for anim_data in anim_datas:
        if anim_data is None:
            return
        nla_tracks = anim_data.nla_tracks
        if not len(nla_tracks):# or len(nla_tracks[:-1]) != len(obj.Anim_Layers):
            return
        override_tracks = anim_layers.check_override_tracks(obj, anim_data)
        for i, track in enumerate(nla_tracks):
            if track == nla_tracks[-1] and track.strips[0].blend_type == 'SUBTRACT' and track.strips[0].action == anim_data.action and track.name != 'Subtract_Layer':
                
                track.name = 'Subtract_Layer'
            #skip if it's not subtract layer or a different anim data type
            if track == nla_tracks[-1] or anim_data != current_anim_data:
                continue
            #make sure there is no other layer with the name Subtract_Layer
            if track.name == 'Subtract_Layer':
                track.name = anim_layers.unique_name([track.name for track in nla_tracks], 'Subtract_Layer')
            #make sure there are no duplicated names
            if track.name != obj.Anim_Layers[i].name:
                #If its an override track, then make sure the reference object name is also synchronized
                if obj.Anim_Layers[i].name in override_tracks:
                    override_tracks[obj.Anim_Layers[i].name].name = track.name
                obj.Anim_Layers[i].name = track.name
                if len(track.strips) == 1:
                    track.strips[0].name = track.name
    
def subscribe_to_track_name(scene):
    '''Subscribe to the name of track'''
    
    #subscribe_track = nla_track.path_resolve("name", False)
    subscribe_track = (bpy.types.NlaTrack, 'name')
    
    bpy.msgbus.subscribe_rna(
        key=subscribe_track,
        # owner of msgbus subcribe (for clearing later)
        owner=scene,
        # Args passed to callback function (tuple)
        args=(),
        # Callback function for property update
        notify=track_update_callback,)
        
    bpy.msgbus.publish_rna(key=subscribe_track)

def action_name_callback(*args):
    '''update layers with the tracks name'''
    if not bpy.context.selected_objects:
        return
    obj = bpy.context.object
    if obj is None:
        return
    if not obj.als.turn_on:
        return
    if not obj.als.auto_rename:
        return
    anim_data = anim_layers.anim_data_type(obj)
    #anim_datas = anim_layers.anim_datas_append(obj)
    if anim_data is None:
        return
    nla_tracks = anim_data.nla_tracks
    if not len(nla_tracks):
        return
    action = anim_data.action
    if action is None:
        return
    layer = obj.Anim_Layers[obj.als.layer_index]
    global action_name
    if 'action_name' not in globals():
        action_name = action.name
    if layer.name != action.name and action.name != action_name:
        layer.name = action.name
    action_name = action.name
    
def subscribe_to_action_name(scene):
    '''Subscribe to the name of track'''
    
    #subscribe_track = nla_track.path_resolve("name", False)
    subscribe_action = (bpy.types.Action, 'name')
    
    bpy.msgbus.subscribe_rna(
        key=subscribe_action,
        # owner of msgbus subcribe (for clearing later)
        owner=scene,
        # Args passed to callback function (tuple)
        args=(),
        # Callback function for property update
        notify=action_name_callback,)
        
    bpy.msgbus.publish_rna(key=subscribe_action)

def blend_update_callback(*args):
    '''update the nla track blend type with the blend type property'''
    if not bpy.context.selected_objects:
        return
    obj = bpy.context.object
    anim_data = anim_layers.anim_data_type(obj)
    if anim_data is None:
        return
    if not len(anim_data.nla_tracks):
        return
    if len(anim_data.nla_tracks[obj.als.layer_index].strips) != 1:
        return
    strip = anim_data.nla_tracks[obj.als.layer_index].strips[0]
    if strip.blend_type not in ['REPLACE', 'ADD', 'SUBTRACT']:
        obj.Anim_Layers[obj.als.layer_index].lock = True
        return
    if obj.als.blend_type != strip.blend_type:
        obj.als.blend_type = strip.blend_type
        anim_layers.redraw_areas('VIEW_3D')

def subscribe_to_blend_type(scene):
    '''Subscribe to the name of track'''
    
    subscribe_blend = (bpy.types.NlaStrip, 'blend_type')
    
    bpy.msgbus.subscribe_rna(
        key=subscribe_blend,
        # owner of msgbus subcribe (for clearing later)
        owner=scene,
        # Args passed to callback function (tuple)
        args=(),
        # Callback function for property update
        notify=blend_update_callback,)
        
    bpy.msgbus.publish_rna(key=subscribe_blend)

def influence_update_callback(*args):
    '''update influence'''
    if not bpy.context.selected_objects:
        return
    obj = bpy.context.object
    #checking if the object has nla tracks, when I used undo it was still calling the property on an object with no nla tracks
    if obj is None:
        return
    if not obj.als.turn_on:
        return
    anim_data = anim_layers.anim_data_type(obj)
    if anim_data is None:
        return
    if not len(anim_data.nla_tracks):
        return
    
    track = anim_data.nla_tracks[obj.als.layer_index]
    if len(track.strips) != 1:
        return

    if track.strips[0].fcurves[0].mute or track.strips[0].fcurves[0].lock:
        return
 
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto and len(track.strips[0].fcurves[0].keyframe_points):
        track.strips[0].keyframe_insert('influence')
        track.strips[0].fcurves[0].update()
        return
    
    #if the influence property and fcurve value are not the same then store the keyframes to check in the handler for a change
    if track.strips[0].influence != track.strips[0].fcurves[0].evaluate(bpy.context.scene.frame_current):
        global influence_keys
        influence_keys = [tuple(key.co) for key in track.strips[0].fcurves[0].keyframe_points]
           
def subscribe_to_influence(scene):
    '''Subscribe to the influence of the track'''
    subscribe_influence = (bpy.types.NlaStrip, 'influence')
    bpy.msgbus.subscribe_rna(
        key=subscribe_influence,
        # owner of msgbus subcribe (for clearing later)
        owner=scene,
        # Args passed to callback function (tuple)
        args=(scene,),
        # Callback function for property update
        notify=influence_update_callback,)
        
    bpy.msgbus.publish_rna(key=subscribe_influence)