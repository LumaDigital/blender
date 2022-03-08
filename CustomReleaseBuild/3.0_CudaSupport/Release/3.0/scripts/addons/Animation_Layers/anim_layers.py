import bpy

from bpy.app.handlers import persistent
from . import bake_ops
from . import subscriptions
from . import addon_updater_ops


@persistent        
def loadanimlayers(self, context):
    '''When loading a file check if the current selected object is with animlayers, if not then check if there is something else turned on'''
    scene = bpy.context.scene
    anim_layer_objects = [AL_item.object for AL_item in scene.AL_objects]
    #if the current object is not turned on, then check if another object is turned on
    subscribe = False
    
    for obj in bpy.context.scene.objects:
        if obj is None:
            continue
        check_overrides_subtrack(obj)             
        if obj.als.turn_on:
            add_obj_to_animlayers(obj, anim_layer_objects)
            if obj.als.layer_index > len(obj.Anim_Layers) - 1:
                obj.als.layer_index = len(obj.Anim_Layers) - 1
            subscribe = True
        elif obj in anim_layer_objects:
            obj.als.turn_on = False
            scene.AL_objects.remove(anim_layer_objects.index(obj))
    if subscribe:
        subscriptions.subscriptions_add(scene)
    
def turn_animlayers_on(self, context):
    '''Turning on and off the NLA with obj.als.turn_on property'''
    obj = self.id_data
    scene = context.scene
    anim_data = anim_data_type(obj)
    #iterate through all selected objects, in case both were checked with alt + click
    if obj is None:
        return
    if self.turn_on:
        #If there are already tracks in the NLA before animation layer, prompt to delete them.
        check_anim_data_start(obj, anim_data)
        if len(obj.Anim_Layers):
            start_animlayers(obj)
    else:           
        #Remove object from animlayers collection
        for i, AnimLayers in enumerate(scene.AL_objects):
            if AnimLayers.object == obj:
                scene.AL_objects.remove(i)
                break

        if obj.type == 'MESH':
            if hasattr(obj.data.shape_keys, 'animation_data'):
                obj.data.shape_keys.animation_data.use_nla = False
                remove_sub_track(obj.data.shape_keys.animation_data)
        
        if obj.animation_data is None:
            #continue
            return
        obj.animation_data.use_nla = False 
        remove_sub_track(obj.animation_data)

        #iterate only over object animation, not shapekeys and apply the last replace layer
        for track in reversed(obj.animation_data.nla_tracks):
            if not len(track.strips) or track.mute:
                continue
            #when turned off select the 'replace' base layer or action as the active action
            if track.strips[0].blend_type == 'REPLACE' or track == obj.animation_data.nla_tracks[0]:
                obj.animation_data.action = track.strips[0].action
                break
        #if there are no objects in AL_objects then subsciptions will be removed
        subscriptions.subscriptions_remove()

def start_animlayers(obj):
    scene = bpy.context.scene
    AnimLayer_objects = [AnimLayers.object for AnimLayers in scene.AL_objects]
    if not len(scene.AL_objects):
        subscriptions.subscriptions_add(scene)
    if obj not in AnimLayer_objects:
        add_obj_to_animlayers(obj, AnimLayer_objects)

    anim_data = anim_data_type(obj) 
    if not hasattr(anim_data, 'nla_tracks'):
        return
    anim_data.action_blend_type = 'ADD'
    if not len(anim_data.nla_tracks):
        return
    anim_data.nla_tracks[0].is_solo = False
    nla_tracks = anim_data.nla_tracks

    #check for tracks with duplicated names and assign with unique name
    track_names = [track.name for track in nla_tracks]
    for i, name in enumerate(track_names):
        if track_names.count(name) > 1:
            track_names[i] = unique_name(track_names, name)
            nla_tracks[i].name = track_names[i]
            if len(nla_tracks[i].strips) == 1:
                nla_tracks[i].strips[0].name = track_names[i]
    register_layers(obj, nla_tracks)
    
    for i, layer in enumerate(obj.Anim_Layers):
        if len(nla_tracks[i].strips) != 1:
            continue
        if layer.influence != nla_tracks[i].strips[0].influence and layer.influence != -1:
            layer.influence = nla_tracks[i].strips[0].influence
            
    if len(obj.Anim_Layers):
        obj.als.layer_index = obj.als.layer_index

def check_anim_data_start(obj, selected_anim_data):
    '''adds subtract layer and active action of the first layer to animation data that is currently not selected'''
    anim_datas = [obj.animation_data]
    if obj.type == 'MESH':
        if hasattr(obj.data.shape_keys, 'animation_data'):
            anim_datas.append(obj.data.shape_keys.animation_data)

    for anim_data in anim_datas:
        if not hasattr(anim_data, 'nla_tracks'):
            continue
        anim_data.use_nla = True
        if anim_data == selected_anim_data:
            if len(obj.Anim_Layers) and not len(anim_data.nla_tracks):
                obj.Anim_Layers.clear()
            if not len(obj.Anim_Layers) and len(anim_data.nla_tracks):
                bpy.ops.message.warning('INVOKE_DEFAULT')
            continue
        if not len(anim_data.nla_tracks):
             continue
        if len(anim_data.nla_tracks[-1].strips) == 1:
            strip = anim_data.nla_tracks[-1].strips[0]
            if strip.blend_type == 'SUBTRACT' and strip.action == anim_data.action:
                continue
        #use the action from the current layer
        anim_data.action = anim_data.nla_tracks[obj.als.layer_index].strips[0].action
        add_substract_layer(anim_data.nla_tracks, anim_data.action)

def add_obj_to_animlayers(obj, anim_layer_objects):
    '''Add the current object to the scene animation layers'''
    if obj in anim_layer_objects or obj is None or not obj.als.turn_on:
        return
    new_obj = bpy.context.scene.AL_objects.add()
    new_obj.object = obj
    new_obj.name = new_obj.object.name
    anim_data = anim_data_type(obj)
    if anim_data is None:
        return
    if anim_data.action is not None:
        new_obj.fcurves = len(anim_data.action.fcurves)
    else:
        if not len(anim_data.nla_tracks):
            return
        track = anim_data.nla_tracks[obj.als.layer_index]
        if len(track.strips) != 1:
            return
        anim_data.action = track.strips[0].action

def register_layers(obj, nla_tracks):
    #check if the top track can be assigned as a subtrack
    update_sub_track(nla_tracks, obj)
    visible_layers(obj, nla_tracks)
    #apply the correct setup for the strips. If there are more then one strip then lock the layer
    for i, track in enumerate(nla_tracks[:-1]):
        if track.is_solo:
            track.is_solo = False
            obj.Anim_Layers[i].solo = True
            
        if len(track.strips) != 1 or track.strips[0].type == 'META' and len(obj.Anim_Layers) > i+1:
            obj.Anim_Layers[i].lock = True
            continue
        strip = track.strips[0]
        strip.action_frame_start = 0
        strip.frame_start = 0
        strip.use_sync_length = False
        use_animated_influence(strip)
        if not len(strip.fcurves[0].keyframe_points):
            obj.Anim_Layers[i].influence = strip.influence
              
#updating the ui list with the nla track names
def visible_layers(obj, nla_tracks):
    '''Creates a list of all the tracks without the top subtrack for the UI List'''
    mute = []
    lock = []
    solo = []

    #store all the layer properties
    for layer in obj.Anim_Layers:
        mute.append(layer.mute)
        lock.append(layer.lock)
        solo.append(layer.solo)
    
    #check if a layer was removed and adjust the stored properties
    if len(nla_tracks[:-1]) < len(obj.Anim_Layers):
        removed = 0
        for i, layer in enumerate(obj.Anim_Layers):
            if layer.name not in nla_tracks:
                mute.pop(i - removed)
                lock.pop(i - removed)
                solo.pop(i - removed)
                removed += 1
               
    #check if a layer was added and adjust the stored properties
    if len(nla_tracks[:-1]) > len(obj.Anim_Layers):
        obj.Anim_Layers.update()
        for i, track in enumerate(nla_tracks[:-1]):
            if track.name not in obj.Anim_Layers: 
                mute.insert(i, False)
                lock.insert(i, False)
                solo.insert(i, False)
                    
    #write layers             
    obj.Anim_Layers.clear()
    #check if there are still layers because of overrides
    length = len(obj.Anim_Layers)
    for i, track in enumerate(nla_tracks[:-1]):
        if length > i:
            continue
        layer = obj.Anim_Layers.add()
        layer.name = track.name
        if len(track.strips) == 1:
            track.strips[0].name = track.name
        if mute:
            layer.mute = mute[i]
            layer.lock = lock[i]
            if solo[i]:
                layer.solo = solo[i]  
        
def use_animated_influence(strip):
    if strip.use_animated_influence:
        return
    strip.use_animated_influence = True
    strip.keyframe_delete(strip.fcurves[0].data_path, frame=0)
    strip.influence = 1 
 
def check_overrides_ALobjects(obj):
    #check if an override object was added and already had animlayers turnedon
    if not obj.override_library:
        return
    scene = bpy.context.scene
     
    if obj.name in scene.AL_objects:
        return
    if not scene.AL_objects:
        subscriptions.subscriptions_add(scene)
    anim_layer_objects = [AL_item.object for AL_item in scene.AL_objects]
    add_obj_to_animlayers(obj, anim_layer_objects)
    
    check_overrides_subtrack(obj)
    
def check_overrides_subtrack(obj):
    #if it's an override object that was recently linked to the scene then remove the subtract from the reference file
    if obj.override_library is None:
        return
    if obj.override_library.reference.animation_data is None:
        return
    if obj.als.data_type == 'OBJECT':
        nla_tracks_ref = obj.override_library.reference.animation_data.nla_tracks
    else:
        nla_tracks_ref = obj.override_library.reference.data.shape_keys.animation_data.nla_tracks
    anim_layers_ref = obj.override_library.reference.Anim_Layers
    if not len(anim_layers_ref):
        return
    if len(nla_tracks_ref[-1].strips) != 1:
        return
    
    if nla_tracks_ref[-1].name in anim_layers_ref or nla_tracks_ref[-1].strips[0].blend_type != 'SUBTRACT':
        return

    anim_data = anim_data_type(obj)
    for track in anim_data.nla_tracks:
        
        if nla_tracks_ref[-1].strips[0].name == track.strips[0].name and track.strips[0].blend_type == 'SUBTRACT':
            #remove locally
            anim_data.nla_tracks.remove(track)

def remove_sub_track(anim_data):
    if not len(anim_data.nla_tracks):
        return
    if not len(anim_data.nla_tracks[-1].strips):
        return
    track = anim_data.nla_tracks[-1]
    strip = track.strips[0]
    if strip.blend_type == 'SUBTRACT' and strip.action == anim_data.action:
        anim_data.nla_tracks.remove(track)

def add_substract_layer(nla_tracks, action):
    sub_track = nla_tracks.new()
    sub_track.name = "Subtract_Layer"
    #if the action is empty then add a temporary action for creating the strip and then remove it
    if action is None:
        action = bpy.data.actions[0]
        remove = True
    else:
        remove = False
    sub_strip = sub_track.strips.new(name='Subtract_strip',start=0, action=action)
    #If there was no action then remove it
    if remove:
        sub_strip.action = None
    sub_strip.name = 'Subtract_strip'
    sub_strip.action_frame_start = 0
    subscriptions.frameend_update_callback(bpy.context.scene)
    sub_strip.blend_type = 'SUBTRACT'
    sub_track.lock = True
    return sub_track

def update_sub_track(nla_tracks, obj):
    #check if the last layer is already a subtract layer and assign it to sub_track
    if len(nla_tracks[-1].strips) and len(nla_tracks) > 1:
        if nla_tracks[-1].strips[0].blend_type == 'SUBTRACT':
            sub_track = nla_tracks[-1]
            return sub_track
           
    #If tracks were removed then update als.layer_index into index property
    if obj.als.layer_index > len(nla_tracks)-1:
        index = len(nla_tracks)-1
    else:
        index = obj.als.layer_index
        
    #make sure there is a strip with an action before adding a subtrack
    if len(nla_tracks[index].strips):
        action = nla_tracks[index].strips[0].action
    else:
        action = None
    sub_track = add_substract_layer(nla_tracks, action)
    return sub_track

#################################################### Multiply layer view FUNCTIONS ############################################################################
def store_keyframes(fcu, keyframes):
    for key in fcu.keyframe_points:
        if key.co[0] not in keyframes:
            keyframes.append(key.co[0])
            
    return keyframes

def hide_view_all_keyframes(obj, anim_data):
    '''hide view all keyframes in the graph editor, to avoid the user changing the values
    and lock channels when edit all keyframes is turned off'''
    
    if anim_data is None:
        return
    if anim_data.action is None:
        return
    if len(anim_data.action.fcurves):
        return
    for i, layer in enumerate(obj.Anim_Layers):
        if layer.lock or obj.als.layer_index == i:
            continue
        fcu = anim_data.action.fcurves.find(layer.name, index = i)
        if fcu is None:
            continue
        
        if not obj.als.edit_all_keyframes and not fcu.group.lock: #lock the groups if edit is not selected
            fcu.group.lock = True
        
        if bpy.context.area:    
            if bpy.context.area.type != 'GRAPH_EDITOR': #hide the channels when using graph editor
                return
        
        if not fcu.hide:
            fcu.hide = True

def fcurve_bones_path(obj, fcu):
    '''if only selected bones is used then check for the bones path in the fcurves data path'''
    if obj.als.only_selected_bones and obj.mode == 'POSE':
        selected_bones_path = [bone.path_from_id() for bone in bpy.context.selected_pose_bones]
        if fcu.data_path.split('].')[0]+']' not in selected_bones_path:
            return True
    return False
 
def edit_all_keyframes():
    obj = bpy.context.object
    anim_data = anim_data_type(obj)
    
    for i, layer in enumerate(obj.Anim_Layers): #look for the Anim Layers fcurve
        if layer.lock or anim_data.action is None or i == obj.als.layer_index:
            continue
        fcu = anim_data.action.fcurves.find(layer.name, index = i)
        if fcu is None or not len(fcu.keyframe_points):
            continue
        
        #check if keyframes were deleted
        if len(fcu_layers[fcu.data_path]) != len(fcu.keyframe_points) and bpy.context.active_operator.name == 'Delete Keyframes':
            keyframes = store_keyframes(fcu, [])
            del_keys = list(set(fcu_layers[fcu.data_path]) - set(keyframes))
            for fcurve in anim_data.nla_tracks[i].strips[0].action.fcurves: #delete the relative keyframes in the action
                if fcurve_bones_path(obj, fcurve):
                    continue
                if fcurve.group is not None:
                    if fcurve.group.name == 'Anim Layers':
                        continue
                #del_keyframes = [keyframe for keyframe in fcurve.keyframe_points if keyframe.co[0] in del_keys]
                keyframe_points = list(fcurve.keyframe_points)
                while keyframe_points: # remove the keyframes from the original action
                    if keyframe_points[0].co[0] in del_keys:
                        fcurve.keyframe_points.remove(keyframe_points[0])
                        keyframe_points = list(fcurve.keyframe_points)
                    else:
                        keyframe_points.pop(0)
                fcurve.update()
            keyframes = [key for key in keyframes if key not in del_keys]
            fcu_layers.update({fcu.data_path : keyframes})
            continue
            
        #check if keyframes were moved to a different location
        old_keys = {}
        for key in fcu.keyframe_points: #creates dictionary of the old key frame values with their difference
            if key.co[0] != key.co[1]:
                old_keys.update({key.co[1] : key.co[0] - key.co[1]})
                key.co[1] = key.co[0]  # reset the keyframe
                
        #iterate through the fcurves in the original action    
        for fcurve in anim_data.nla_tracks[i].strips[0].action.fcurves:
            if fcurve_bones_path(obj, fcurve):
                continue
            for keyframe in fcurve.keyframe_points:
                if keyframe.co[0] not in old_keys:
                    continue
                difference = old_keys[keyframe.co[0]]
                keyframe.co[0] = keyframe.co[0] + difference
                if keyframe.interpolation == 'BEZIER':
                    keyframe.handle_left[0] += difference
                    keyframe.handle_right[0] += difference
            #fcurve.update()
                
def view_all_keyframes(self, context):
    '''Creates new fcurves with the keyframes from the all the layers'''
    obj = self.id_data
    anim_data = anim_data_type(obj)
    #if animation layers is still not completly loaded then return
    if len(anim_data.nla_tracks[:-1]) != len(obj.Anim_Layers) or anim_data.action is None:
        return
    #remove old Anim Layers fcurves
    for i, track in enumerate(anim_data.nla_tracks[:-1]):
        fcu = anim_data.action.fcurves.find(track.name, index=i)    
        if fcu: #remove all the fcurves/channels in the group and mark as removed
            if fcu.group.name == 'Anim Layers':
                fcu.group.lock = False
                for fcu_remove in fcu.group.channels:
                    anim_data.action.fcurves.remove(fcu_remove)
                break
    if not self.view_all_keyframes: #If the option is uncheck then finish edit and return
        self.edit_all_keyframes = False
        return

    global fcu_layers        
    fcu_layers = {}      
    for i, track in enumerate(anim_data.nla_tracks[:-1]):
        if i == obj.als.layer_index or track.strips[0].action is None or not len(track.strips[0].action.fcurves) or obj.Anim_Layers[i].lock:
            continue
        #create a new fcurve with the name of the track
        fcu_layer = anim_data.action.fcurves.new(track.name, index=i, action_group='Anim Layers')
        fcu_layer.update()
        fcu_layer.is_valid = True
        keyframes = []
        #store all the keyframe locations from the fcurves of the layer
        for fcu in track.strips[0].action.fcurves:
            if fcu.group is not None:
                if fcu.group.name == 'Anim Layers': 
                    continue
            #if only selected bones is used then check for the bones
            if obj.als.only_selected_bones and obj.mode == 'POSE':
                selected_bones = [bone.path_from_id() for bone in context.selected_pose_bones]
                if fcu.data_path.split('].')[0]+']' not in selected_bones:
                    continue
                
            keyframes = store_keyframes(fcu, keyframes)          
        if not keyframes:
            continue
        
        for key in keyframes: #create new keyframes for all the stored keys
            fcu_layer.keyframe_points.add(1)
            
            fcu_layer.keyframe_points[-1].co[0] = key
            fcu_layer.keyframe_points[-1].co[1] = key
            fcu_layer.keyframe_points[-1].interpolation = 'LINEAR'
            fcu_layer.keyframe_points[-1].type = self.view_all_type    
            
        fcu_layer.hide = True
        fcu_layer.update()
        #store the fcurves and keyframes
        fcu_layers.update({fcu_layer.data_path : keyframes})
        
        
        #Make sure lock is turned off when selecting new layer and edit is turned on
        if fcu_layer is not None and self.edit_all_keyframes:
            fcu_layer.group.lock = False 

###################################################### PROPERTY FUNCTIONS ################################################
def update_layer_index(self, context):
    '''select the new action clip when there is a new selection in the ui list and make all the updates for this Layer'''
    obj = self.id_data
    if obj is None:
        return
    if not self.turn_on:
        return
    if not len(obj.Anim_Layers):
        return
    anim_data = anim_data_type(obj)
    
    #check first if the layer is locked turn off everything and return when locked
    if obj.Anim_Layers[obj.als.layer_index].lock:
        anim_data.action = None
        anim_data.action_influence = 0
        if len(anim_data.nla_tracks[-1].strips):
            anim_data.nla_tracks[-1].strips[0].action = None
        return
        
    #activate the current action of the layer
    anim_data.action_influence = 1
    current_action = anim_data.nla_tracks[obj.als.layer_index].strips[0].action
    anim_data.action = current_action
    anim_data.nla_tracks[-1].strips[0].action = current_action
    strip = anim_data.nla_tracks[obj.als.layer_index].strips[0]
    obj.als.blend_type = strip.blend_type
    use_animated_influence(strip)
    obj.als.view_all_keyframes = obj.als.view_all_keyframes

    if obj.name in context.scene.AL_objects:
        if current_action is not None:
            context.scene.AL_objects[obj.name].fcurves = len(anim_data.action.fcurves)
        else:
            context.scene.AL_objects[obj.name].fcurves = 0

def layer_mute(self, context):
    obj = self.id_data
    index = list(obj.Anim_Layers).index(self)
    anim_data = anim_data_type(obj)
    anim_data.nla_tracks[index].mute = self.mute
    
    #Exclude muted layers from view all keyframes
    if obj.als.view_all_keyframes:
        obj.als.view_all_keyframes = True
    
def layer_solo(self, context):
 
    obj = context.object
    anim_data = anim_data_type(obj)
    #added a skip boolean so that when layer.solo = False it doesnt iterate through all the layers because of the call, since only one layer can be solo
    global skip
    try:
        if skip:
            return
    except NameError:
        skip = False

    if self.solo:
        for i, layer in enumerate(obj.Anim_Layers):
            if layer != self:
                skip = True
                layer.solo = False
                anim_data.nla_tracks[i].mute = True
            else:
                anim_data.nla_tracks[i].mute = False
        skip = False
    else:
        #when turned off restore track mute from the layers mute property
        for i, track in enumerate(anim_data.nla_tracks[:-1]):
            track.mute = obj.Anim_Layers[i].mute
   
def layer_lock(self, context):

    obj = self.id_data
    index = list(obj.Anim_Layers).index(self)
    anim_data = anim_data_type(obj)
    nla_tracks = anim_data.nla_tracks
    
    if not self.lock:
        if len(nla_tracks[index].strips) != 1 or nla_tracks[index].strips[0].type == 'META' or nla_tracks[index].strips[0].blend_type not in {'REPLACE','ADD','SUBTRACT'}:
            self.lock = True
    if index == obj.als.layer_index:
        obj.als.layer_index = obj.als.layer_index
        
    #Exclude locked layers from view all keyframes
    if obj.als.view_all_keyframes:
        obj.als.view_all_keyframes = True
         
def only_selected_bones(self, context):
    '''assign selected bones to a global variable that will be checked in the handler'''
    if self.only_selected_bones:
        global selected_bones
        selected_bones = context.selected_pose_bones
        view_all_keyframes(self, context)
    else:
        view_all_keyframes(self, context)
        del selected_bones
    
def data_type_update(self, context):
    obj = self.id_data
    anim_data = anim_data_type(obj)
    if anim_data is None:
        obj.Anim_Layers.clear()
        return
    if not len(anim_data.nla_tracks):
        obj.Anim_Layers.clear()
        return
    obj.als.layer_index = 0
    register_layers(obj, anim_data.nla_tracks)
    
    #change bake method if working with shapekeys
    if self.baketype == 'BLENDER' and self.data_type == 'KEY':
        self.baketype = 'AL'

def layer_name_update(self, context):
    
    #if layer name exists then add a unique name
    obj = self.id_data
    layer_names = [layer.name for layer in context.object.Anim_Layers if layer != self]
    if self.name in layer_names:
        self.name = unique_name(layer_names, self.name)
    anim_data = anim_data_type(obj)
    if not hasattr(anim_data, 'nla_tracks'):
        return
    nla_tracks = anim_data.nla_tracks
    index = list(obj.Anim_Layers).index(self)
    if self.name != nla_tracks[index].name:
        nla_tracks[index].name = self.name
        if len(nla_tracks[index].strips) == 1:
            nla_tracks[index].strips[0].name = self.name

def influence_mute_update(self, context):
    '''added an extra property for the influence mute because it was disabled with override libraries'''
    obj = self.id_data
    if not len(obj.Anim_Layers):
        return
    index = obj.Anim_Layers.find(self.name)
    anim_data = anim_data_type(obj)
    strip = anim_data.nla_tracks[index].strips[0]
    fcu = strip.fcurves[0]
    fcu.mute = self.influence_mute
    fcu.lock = self.influence_mute
    if self.influence_mute:
         self.influence = strip.influence

def influence_update(self, context):
    obj = self.id_data
    if not len(obj.Anim_Layers):
        return
    index = obj.Anim_Layers.find(self.name)
    anim_data = anim_data_type(obj)
    strip = anim_data.nla_tracks[index].strips[0]
    strip.influence = self.influence
    strip.fcurves[0].update()
    
def blend_type_values(self, obj, strip):
    '''Changing the values for scale and rotation_quaternion when switching between blend modes'''
    if obj.als.data_type != 'OBJECT':
        return
    if obj.animation_data.action is None:
        return
    if not len(obj.animation_data.action.fcurves):
        return
    for fcu in strip.action.fcurves:
        if 'scale' not in fcu.data_path and 'rotation_quaternion' not in fcu.data_path:
            continue
        default_value = bake_ops.attr_default(obj, (fcu.data_path, fcu.array_index))
        #switching from replace to add layer, needs to reduce value of 1 from the scale and rotation_quaternion
        for keyframe in fcu.keyframe_points:
            if strip.blend_type == 'REPLACE' and (self.blend_type == 'ADD' or self.blend_type == 'SUBTRACT'):
                keyframe.co[1] -= default_value
                keyframe.handle_right[1] -= default_value
                keyframe.handle_left[1] -= default_value
            elif (strip.blend_type == 'ADD' or strip.blend_type == 'SUBTRACT') and self.blend_type == 'REPLACE':
                keyframe.co[1] += default_value
                keyframe.handle_right[1] += default_value
                keyframe.handle_left[1] += default_value

def blend_type_update(self, context):
    '''synchronize the blend property with the NLA Blend'''
    obj = self.id_data
    anim_data = anim_data_type(obj)
    strip = anim_data.nla_tracks[obj.als.layer_index].strips[0]
    if self.blend_type == strip.blend_type:
        return
    if obj.als.auto_blend:
        blend_type_values(self, obj, strip)
    strip.blend_type = self.blend_type

def auto_rename(self, context):
    '''Use auto rename when Turning it on'''
    if not self.auto_rename:
        return
    obj = self.id_data
    if obj is None:
        return
    anim_data = anim_data_type(obj)
    if anim_data is None:
        return
    if anim_data.action is None:
        return
    name = anim_data.action.name
    obj.Anim_Layers[obj.als.layer_index].name = name
    anim_data.nla_tracks[obj.als.layer_index].name = name
    anim_data.nla_tracks[obj.als.layer_index].strips[0].name = name
    
def unlock_edit_keyframes(self, context):
    '''Lock or unlock the fcurves of the Multiple layers with the edit all keyframes property'''
    obj = self.id_data
    if not self.view_all_keyframes or obj is None:
        return
    anim_data = anim_data_type(obj)
    for i, layer in enumerate(obj.Anim_Layers): #look for the Anim Layers fcurve
        if layer.lock or anim_data.action is None or i == obj.als.layer_index:
            continue
        fcu = anim_data.action.fcurves.find(layer.name, index = i)
        if self.edit_all_keyframes:
            fcu.group.lock = False
        else:
            fcu.group.lock = True
        return   

def action_items(self, context):
    obj = self.id_data
    return list(map(lambda id_item: (id_item.name, id_item.name, id_item.name), [action for action in bpy.data.actions if action.id_root == obj.als.data_type]))

def load_action(self, context):
    '''Load a new action from the layer list'''
    obj = self.id_data
    index = obj.Anim_Layers.find(self.name)
    anim_data = anim_data_type(obj)
    if self.lock:
        return
    strip = anim_data.nla_tracks[index].strips[0]
    action = bpy.data.actions[self.action]
    if index == obj.als.layer_index:
        anim_data.action = action
        anim_data.nla_tracks[-1].strips[0].action = action
    strip.action = action
    if action is None:
        return
    if obj.als.auto_blend and len(action.fcurves):
        strip.blend_type = auto_blendtype(obj, action, strip.blend_type)
    #Auto rename
    if obj.als.auto_rename:
        obj.Anim_Layers[index].name = action.name
        anim_data.nla_tracks[index].name = action.name
        strip.name = action.name
    obj.als.view_all_keyframes = obj.als.view_all_keyframes

def auto_blendtype(obj, action, current_blend):
    '''apply blend type automatically'''
    if not len(action.fcurves):
        return current_blend
    count = 0
    for fcu in action.fcurves:
        if not 'scale' in fcu.data_path and not 'rotation_quaternion' in fcu.data_path:
            continue
        default_value = bake_ops.attr_default(obj, (fcu.data_path, fcu.array_index))
        if not default_value:
            continue
        count += 1
        for keyframe in fcu.keyframe_points:
            if keyframe.co[1] == 0:
                return 'ADD' 
    if count:
        return 'REPLACE'
    else:
        return current_blend

         
###################################################### HELPER FUNCTIONS ################################################                
def redraw_areas(areas):
    for area in bpy.context.window_manager.windows[0].screen.areas:
        if area.type in areas:
            area.tag_redraw()

def anim_data_type(obj, toggle = False):    
    if obj.als.data_type == 'OBJECT' and not toggle:
        if not hasattr(obj, 'animation_data'):
            return None
        anim_data = obj.animation_data
    else:
        if not hasattr(obj.data.shape_keys, 'animation_data'):
            return None
        anim_data = obj.data.shape_keys.animation_data
    
    return anim_data

def anim_datas_append(obj):
    '''append shapekey animation data if it also exists'''
    anim_datas = [obj.animation_data]
    if obj.type == 'MESH':
        if hasattr(obj.data.shape_keys, 'animation_data'):
            #anim_datas = {obj.animation_data, obj.data.shape_keys.animation_data}
            anim_datas.append(obj.data.shape_keys.animation_data)
    return anim_datas

def unique_name(collection, name):
    '''add numbers to tracks if they have the same name'''
    if name not in collection:
        return name
    nr = 1
    if '.' in name:
        end = name.split('.')[-1]
        if end.isnumeric():
            nr = int(end)
            name = '.'.join(name.split('.')[:-1])
    while name + '.' + str(nr).zfill(3) in collection:
        nr += 1
    return name + '.' + str(nr).zfill(3)

#checks if the object has an action and if it exists in the NLA
def action_search(action, nla_tracks):
    if action != None:
        for track in nla_tracks:
            for strip in track.strips:
                if strip.action == action:
                    return True                   
    else:
        return True
    
    return False

def delete_layers(obj, nla_tracks):
    for track in nla_tracks:
        if track.select == True:
            nla_tracks.remove(track)
    visible_layers(obj, nla_tracks)

def select_layer_bones(self, context):
    obj = context.object
    strips = obj.animation_data.nla_tracks[obj.als.layer_index].strips
    if len(strips) != 1 or strips[0].action is None:
        return
    for fcu in strips[0].action.fcurves:
        if 'pose.bones' in fcu.data_path:
            bone = fcu.data_path.split('"')[1]
            if bone in obj.data.bones:
                obj.data.bones[bone].select = True

###################################################### CLASSES ###########################################################
class SelectBonesInLayer(bpy.types.Operator):
    """Select bones with keyframes in the current layer"""
    bl_idname = "anim.bones_in_layer"
    bl_label = "Select layer bones"
    bl_icon = "BONE_DATA"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.object.mode == 'POSE'
    
    def execute(self, context):
        select_layer_bones(self, context)
        return {'FINISHED'}
       
class ClearNLA(bpy.types.Operator):
    bl_idname = "message.warning"
    bl_label = "WARNING!"
    bl_icon = "ERROR"
    
    confirm: bpy.props.BoolProperty(default=True)
    
    def execute(self, context):
        obj = context.object
        anim_datas = anim_datas_append(obj)
        for anim_data in anim_datas:
            if anim_data is None:
                continue
            if self.confirm:
                for track in anim_data.nla_tracks:
                    track.select = True
                delete_layers(obj, anim_data.nla_tracks)
            else:
                start_animlayers(obj)
            
        return {'FINISHED'}
    
    def invoke(self, context, event):
             
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        obj_name = bpy.context.object.name
        col.label(text=obj_name+" has already tracks in the NLA editor, which have been created before using animation layers.")
        row = col.row()
        row.alignment = 'CENTER'
        row.prop(self, "confirm", text="Remove NLA tracks")

def setup_new_layer(obj, anim_data, new_track, Duplicate, blend_type):
    #check if the object already has an action and if it exists in the NLA, if not create a new one
    if action_search(anim_data.action, anim_data.nla_tracks) and not Duplicate:
        new_action = bpy.data.actions.new(name=new_track.name)
        new_action.id_root = obj.als.data_type
    else:
        new_action = anim_data.action
    
    #strip settings
    new_strip = new_track.strips.new(name = new_track.name,start=0, action = new_action)
    new_strip.action_frame_start = 0
    subscriptions.frameend_update_callback(bpy.context.scene)
    new_strip.blend_type = blend_type
    use_animated_influence(new_strip)

    return new_action

def add_animlayer(layer_name = 'Anim_Layer' , duplicate = False, index = 1, blend_type = 'ADD'):
    '''Add an animation layer'''
    obj = bpy.context.object
    check_overrides_ALobjects(obj)
    anim_data = anim_data_type(obj)
    nla_tracks = anim_data.nla_tracks
    previous = None if index == 0 else nla_tracks[obj.als.layer_index]
    
    new_track = nla_tracks.new(prev = previous)
    new_track.name = layer_name
    new_track.lock = True
    setup_new_layer(obj, anim_data, new_track, duplicate, blend_type) 

    return new_track
        
#adding a new track, action and strip       
class AddAnimLayer(bpy.types.Operator):
    """Add animation layer"""
    bl_idname = "anim.add_anim_layer"
    bl_label = "Add Animation Layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.object
        #If adding a shapekey action, then make sure it has at least one shapekey
        if not len(obj.Anim_Layers):
            start_animlayers(obj)
        subscriptions.subscriptions_remove()
        anim_data = anim_data_type(obj)
        
        if obj.als.data_type == 'OBJECT':
            layer_name = 'Anim_Layer'
            base_name = 'Base_Layer'
            if anim_data is None:
                anim_data = obj.animation_data_create()
        elif obj.als.data_type == 'KEY':
            if not obj.data.shape_keys:
                obj.shape_key_add(name = 'Basis')
            layer_name = 'Shapekeys_Layer'
            base_name = 'Base_Shapekeys'
            if anim_data is None:
                anim_data = obj.data.shape_keys.animation_data_create()
        
        nla_tracks = anim_data.nla_tracks
        if anim_data.action == None:
            #start_animlayers(obj)
            flag = False
        else:
            flag = True
        
        if not len(nla_tracks):
            add_animlayer(base_name, index = 0, blend_type = 'REPLACE')
            #using a temporary variable instead of calling update_track_list all the time with obj.als.layer_index
            index = 0
            if flag:
                add_animlayer(layer_name)
                index += 1
            add_substract_layer(nla_tracks, anim_data.action)
        else:
            add_animlayer(unique_name(obj.Anim_Layers, layer_name))
            index = obj.als.layer_index + 1
                
        register_layers(obj, nla_tracks)
        
        obj.als.layer_index = index
        
        subscriptions.subscriptions_add(context.scene)
                
        return {'FINISHED'}  

class DuplicateAnimLayer(bpy.types.Operator):
    """Duplicate animation layer"""
    bl_idname = "anim.duplicate_anim_layer"
    bl_label = "Duplicate Animation Layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):    
 
        obj = context.object
        anim_data = anim_data_type(obj)
        nla_tracks = anim_data.nla_tracks

        if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)     
        
        blend = nla_tracks[obj.als.layer_index].strips[0].blend_type
        track_name = nla_tracks[obj.als.layer_index].name
        
        name = unique_name(obj.Anim_Layers, track_name)
        new_track = add_animlayer(layer_name = name, duplicate = True, blend_type = blend)
        
        if obj.als.linked == False:
            new_action = anim_data.action.copy()
            new_track.strips[0].action = anim_data.action = new_action
                    
        register_layers(obj, nla_tracks)
        
        obj.als.layer_index += 1

        if subscriptions.check_handler not in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.append(subscriptions.check_handler)
                
        return {'FINISHED'}

class ExtractSelection(bpy.types.Operator):
    """Extract selected bones to a new Layer"""
    bl_idname = "anim.extract_selected_bones"
    bl_label = "Extract Selected Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj.type == 'ARMATURE' and obj.mode == 'POSE'

    def execute(self, context):     
 
        obj = context.object
        anim_data = anim_data_type(obj)
        nla_tracks = anim_data.nla_tracks
        action = anim_data.action

        if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)    
        
        blend = nla_tracks[obj.als.layer_index].strips[0].blend_type
        track_name = nla_tracks[obj.als.layer_index].name
        
        name = unique_name(obj.Anim_Layers, track_name + ' Extract')
        new_track = add_animlayer(layer_name = name, duplicate = True, blend_type = blend)
        bones_path = [bone.path_from_id() for bone in context.selected_pose_bones]
        bone_names = [bone.name for bone in context.selected_pose_bones]

        #create a new copy of the action
        new_action = action.copy()
        new_track.strips[0].action = new_action
        
        #remove fcurves of the selected bones in the original layer
        for fcu in action.fcurves:
            group = fcu.group.name if fcu.group is not None else None    
            if fcu.data_path.split(']')[0]+']' in bones_path or group in bone_names:
              action.fcurves.remove(fcu)  
        action.fcurves.update()

        #remove all bones that are not selected from the new extracted layer
        for fcu in new_action.fcurves:
            group = fcu.group.name if fcu.group is not None else None 
            if fcu.data_path.split(']')[0]+']' not in bones_path and group not in bone_names:
                new_action.fcurves.remove(fcu)  
        new_action.fcurves.update()
             
        register_layers(obj, nla_tracks)
        
        obj.als.layer_index += 1   

        if subscriptions.check_handler not in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.append(subscriptions.check_handler)
                
        return {'FINISHED'}

class ExtractMarkers(bpy.types.Operator):
    """Extract keyframes from Markers. Usefull for mocap cleanup"""
    bl_idname = "anim.extract_markers"
    bl_label = "Extract Marked keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(context.scene.timeline_markers)

    def execute(self, context):     
 
        obj = context.object
        anim_data = anim_data_type(obj)
        action = anim_data.action
        nla_tracks = anim_data.nla_tracks

        if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)    
        
        blend = nla_tracks[obj.als.layer_index].strips[0].blend_type
        track_name = nla_tracks[obj.als.layer_index].name
        
        name = unique_name(obj.Anim_Layers, track_name + ' Extract')
        new_track = add_animlayer(layer_name = name, duplicate = True, blend_type = blend)
        if obj.type == 'ARMATURE':
            bones_path = [bone.path_from_id() for bone in context.selected_pose_bones]
            bone_names = [bone.name for bone in context.selected_pose_bones]
        #create a new copy of the action
        new_action = action.copy()
        new_track.strips[0].action = new_action
 
        markers = context.scene.timeline_markers
        marked_frames = [marker.frame for marker in markers]
        #remove all bones that are not selected from the new extracted layer
        for fcu in new_action.fcurves:
            if obj.type == 'ARMATURE':
                group = fcu.group.name if fcu.group is not None else None 
                if fcu.data_path.split(']')[0]+']' not in bones_path and group not in bone_names:
                    new_action.fcurves.remove(fcu)
                    continue
            keyframes = fcu.keyframe_points
            #Create a duplicate of all the keyframes
            roundframes = []
            smartkeys = []
            for keyframe in keyframes:
                if round(keyframe.co[0]) in marked_frames and round(keyframe.co[0]) not in roundframes:
                    smartkeys.append(bake_ops.smartkey(keyframe))
                    roundframes.append(round(keyframe.co[0]))
            smartkeys = bake_ops.add_inbetween(smartkeys)
            
            for smartkey in smartkeys:
                smartkey.value = fcu.evaluate(smartkey.frame)
                smartkey.interpolation = 'BEZIER'
            i = 0
            roundframes = []
            while i < len(keyframes):
                if round(keyframes[i].co[0]) not in marked_frames or round(keyframes[i].co[0]) in roundframes:
                    keyframes.remove(keyframes[i])
                else:
                    keyframes[i].interpolation = 'BEZIER'
                    roundframes.append(round(keyframes[i].co[0]))
                    i += 1
            bake_ops.add_interpolations(fcu, smartkeys)
        
        new_action.fcurves.update()
             
        register_layers(obj, nla_tracks)
        
        obj.als.layer_index += 1   

        if subscriptions.check_handler not in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.append(subscriptions.check_handler)
                
        return {'FINISHED'}

class RemoveAnimLayer(bpy.types.Operator):
    """Remove animation layer"""
    bl_idname = "anim.remove_anim_layer"
    bl_label = "Remove Animation Layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        anim_data = anim_data_type(context.object)
        if hasattr(anim_data, 'nla_tracks'):
            return len(anim_data.nla_tracks)
    
    def execute(self, context):

        obj = context.object
        anim_data = anim_data_type(obj)
        nla_tracks = anim_data.nla_tracks
        try:
            obj.Anim_Layers.remove(obj.als.layer_index)
        except TypeError: #library overrides currently can not remove items
            return {'CANCELLED'}  
        nla_tracks.remove(nla_tracks[obj.als.layer_index]) 
        #update the ui list item's index
        if obj.als.layer_index != 0:
            obj.als.layer_index -= 1

        else:
            obj.als.layer_index = 0
        

        #If nothing is left then remove also the sub_track
        if len(nla_tracks) == 1:
            nla_tracks.remove(nla_tracks[0])

        return {'FINISHED'}  

def move_layer(dir):
    window = bpy.context.window
    old_area = window.screen.areas[0].type
    screen = window.screen
    bpy.context.window_manager.windows[0].screen.areas[0].type = 'NLA_EDITOR'
    area = screen.areas[0]
    override = {'window': window, 'screen': screen, 'area': area}
    obj = bpy.context.object
    bpy.ops.anim.channels_select_all(override, action='DESELECT')
    anim_data = anim_data_type(obj)
    anim_data.nla_tracks[obj.als.layer_index].select = True    
    bpy.ops.anim.channels_move(override, direction=dir)
    
    bpy.context.window_manager.windows[0].screen.areas[0].type = old_area   
            
    visible_layers(obj, anim_data.nla_tracks)   
    
class MoveAnimLayerUp(bpy.types.Operator):
    """Move the selected layer up"""
    bl_idname = "anim.layer_move_up"
    bl_label = "Move selected Animation layer up"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        anim_data = anim_data_type(obj)
        if hasattr(anim_data, 'nla_tracks'):
            return len(anim_data.nla_tracks) > 2
        
    def execute(self, context):
        if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)    
               
        obj = context.object
        if obj.als.layer_index < len(obj.animation_data.nla_tracks)-2:
            
            lock = obj.Anim_Layers[obj.als.layer_index].lock
            lock_01 = obj.Anim_Layers[obj.als.layer_index+1].lock
            move_layer('UP')
            #Switch the properties
            obj.Anim_Layers[obj.als.layer_index].solo, obj.Anim_Layers[obj.als.layer_index+1].solo = obj.Anim_Layers[obj.als.layer_index+1].solo, obj.Anim_Layers[obj.als.layer_index].solo
            obj.Anim_Layers[obj.als.layer_index].mute, obj.Anim_Layers[obj.als.layer_index+1].mute = obj.Anim_Layers[obj.als.layer_index+1].mute, obj.Anim_Layers[obj.als.layer_index].mute
            obj.Anim_Layers[obj.als.layer_index].lock = lock_01
            obj.Anim_Layers[obj.als.layer_index+1].lock = lock
            obj.als.layer_index += 1

        if subscriptions.check_handler not in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.append(subscriptions.check_handler)
                 
        return {'FINISHED'}
    
class MoveAnimLayerDown(bpy.types.Operator):
    """Move the selected layer down"""
    bl_idname = "anim.layer_move_down"
    bl_label = "Move selected Animation layer down"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        anim_data = anim_data_type(context.object)
        if hasattr(anim_data, 'nla_tracks'):
            return len(anim_data.nla_tracks) > 2
        
    def execute(self, context):
        if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)    

        obj = context.object
        if obj.als.layer_index > 0:
            
            lock = obj.Anim_Layers[obj.als.layer_index].lock
            lock_01 = obj.Anim_Layers[obj.als.layer_index-1].lock
            move_layer('DOWN')
            obj.Anim_Layers[obj.als.layer_index].solo, obj.Anim_Layers[obj.als.layer_index-1].solo = obj.Anim_Layers[obj.als.layer_index-1].solo, obj.Anim_Layers[obj.als.layer_index].solo
            obj.Anim_Layers[obj.als.layer_index].mute, obj.Anim_Layers[obj.als.layer_index-1].mute = obj.Anim_Layers[obj.als.layer_index-1].mute, obj.Anim_Layers[obj.als.layer_index].mute
            obj.Anim_Layers[obj.als.layer_index].lock = lock_01
            obj.Anim_Layers[obj.als.layer_index-1].lock = lock
            obj.als.layer_index -= 1
            
        if subscriptions.check_handler not in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.append(subscriptions.check_handler)

        return {'FINISHED'}

def copy_modifiers(modifier, mod_list):
    attr = {}
    for key in dir(modifier): #add all the attributes into a dictionary
        value = getattr(modifier, key)
        attr.update({key: value})    
    mod_list.append(attr)

    return mod_list

def paste_modifiers(fcu, mod_list):
    
    for mod in mod_list:
        new_mod = fcu.modifiers.new(mod['type'])
        for attr, value in mod.items():
            if type(value) is float or type(value) is int or type(value) is bool:
                if not new_mod.is_property_readonly(attr):
                    setattr(new_mod, attr, value)

class CyclicFcurves(bpy.types.Operator):
    """Apply Cyclic Fcurve modifiers to all the selected bones and objects"""
    bl_idname = "anim.layer_cyclic_fcurves"
    bl_label = "Cyclic_Fcurves"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        anim_data = anim_data_type(context.object)
        return anim_data.action is not None
    
    def execute(self, context):
        
        transform_types = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']
        for obj in context.selected_objects:        
            for fcu in obj.animation_data.action.fcurves:
                if obj.mode == 'POSE': #apply only to selected bones
                    if obj.als.only_selected_bones:
                        bones = [bone.path_from_id() for bone in context.selected_pose_bones]
                        if fcu.data_path.split('].')[0]+']' not in bones:
                            continue
                    if fcu.data_path in transform_types:
                        continue
                elif obj.mode != 'POSE':
                    if fcu.data_path not in transform_types:
                        continue
                cycle_mod = False
                mod_list = []
                if len(fcu.modifiers):
                    #i = 0
                    while len(fcu.modifiers):
                        modifier = fcu.modifiers[0]
                        if modifier.type == 'CYCLES':
                            cycle_mod = True
                            break
                        else: #if its a different modifier then store and remove it 
                            mod_list = copy_modifiers(modifier, mod_list)
                            fcu.modifiers.remove(fcu.modifiers[0])
                            #fcu.modifiers.update()
                if cycle_mod:
                    continue
                fcu.modifiers.new('CYCLES')
                fcu.update()
                if not len(mod_list):
                    continue #restore old modifiers
                paste_modifiers(fcu, mod_list)
                fcu.modifiers.update()                      
                                    
            redraw_areas(['GRAPH_EDITOR', 'VIEW_3D'])
                
        return {'FINISHED'}
    
class RemoveFcurves(bpy.types.Operator):
    """Remove Cyclic Fcurve modifiers from all the selected bones and objects"""
    bl_idname = "anim.layer_cyclic_remove"
    bl_label = "Cyclic_Remove"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        anim_data = anim_data_type(context.object)
        return anim_data.action is not None
    
    def execute(self, context):
        
        transform_types = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']
        for obj in context.selected_objects: 
            for fcu in obj.animation_data.action.fcurves:
                if obj.mode == 'POSE': #apply only to selected bones
                    if obj.als.only_selected_bones:
                        bones = [bone.path_from_id() for bone in context.selected_pose_bones]
                        if fcu.data_path.split('].')[0]+']' not in bones:
                            continue
                    if fcu.data_path in transform_types:
                        continue
                # object mode always applies to bones and object mode to objects.
                elif obj.mode != 'POSE':
                    if fcu.data_path not in transform_types:
                        continue

                if len(fcu.modifiers):
                    for mod in fcu.modifiers:
                        
                        if mod.type == 'CYCLES':
                            fcu.modifiers.remove(mod)
                            fcu.update()
                            for area in context.window_manager.windows[0].screen.areas:
                                if area.type == 'GRAPH_EDITOR' or area.type == 'VIEW_3D':
                                    area.tag_redraw()
                            break
        return {'FINISHED'}

class ResetLayerKeyframes(bpy.types.Operator):
    """Add keyframes with 0 Value to the selected object/bones in the current layer, usefull for additive layers"""
    bl_idname = "anim.layer_reset_keyframes"
    bl_label = "Reset_Layer_Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.object.Anim_Layers)

    def execute(self, context):
        obj = context.object
        anim_data = anim_data_type(obj)
        transform_types = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']
        fcurves = anim_data.action.fcurves
        frame_current = context.scene.frame_current
        for fcu in fcurves:
            if obj.type == 'ARMATURE': #apply only to selected bones
                if obj.mode == 'POSE' and fcu.data_path in transform_types: #skip 
                    continue
                elif obj.mode == 'POSE' and obj.als.only_selected_bones:
                    bones = [bone.path_from_id() for bone in context.selected_pose_bones]
                    if fcu.data_path.split('].')[0]+']' not in bones:# and fcu.data_path not in transform_types:
                        continue 
                elif obj.mode == 'OBJECT' and fcu.data_path not in transform_types:
                    continue
           
            value = 0
            key_exists = False
            blend_types = {'REPLACE', 'COMBINE'}
            if 'scale' in fcu.data_path and anim_data.nla_tracks[obj.als.layer_index].strips[0].blend_type in blend_types:
                value = 1
            #check if a key already exists on in the current frame
            for key in fcu.keyframe_points:
                if key.co[0] == frame_current:
                    key.co[1] = value
                    key_exists = True
                    fcu.update()
                    continue
            if key_exists:
                continue
            #if key doesnt exists then add keyframes in current frame
            fcu.keyframe_points.add(1)
            fcu.keyframe_points[-1].co = (frame_current, value)
            fcu.update() 
        return {'FINISHED'}
  
class LAYERS_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, reversed):
        obj = bpy.context.object
        anim_data = anim_data_type(obj)
        self.use_filter_sort_reverse = True
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            #row = layout.row()
            row = layout.row(align = True)
            icon = 'SOLO_ON' if item.solo else 'SOLO_OFF'
            row.prop(item,'solo', text = '', invert_checkbox=False, icon = icon, emboss=False)
            split = row.split(factor=0.1, align = True)
            split.prop(item, "action", icon_only = True, emboss = False)
            split.prop(item, "name", text="", emboss=False)
            split = row.split(factor=0, align = True)
            icon = 'HIDE_ON' if item.mute else 'HIDE_OFF'
            split.prop(item,'mute', text = '', invert_checkbox=False, icon = icon, emboss=False)
            
            icon = 'LOCKED' if item.lock else 'UNLOCKED'
            split.prop(item,'lock', text = '', invert_checkbox=False, icon = icon, emboss=False)
            
        elif self.layout_type in {'GRID'}:
            pass
        
    def invoke(self, context, event):
        pass 
    
class ANIMLAYERS_PT_Panel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    #bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return len(bpy.context.selected_objects)

class ANIMLAYERS_PT_List(ANIMLAYERS_PT_Panel, bpy.types.Panel):
    bl_label = "Animation Layers"
    bl_idname = "ANIMLAYERS_PT_List"

    def draw(self, context):
        obj = context.object
        if obj is None:
            return
        anim_data = anim_data_type(obj)
        layout = self.layout
        
        addon_updater_ops.check_for_update_background()
        
        # could also use your own custom drawing
        # based on shared variables

        # call built-in function with draw code/checks
        addon_updater_ops.update_notice_box_ui(self, context)
                        
        row = layout.row()
        row.prop(obj.als, 'turn_on')
        
        if not obj.als.turn_on:
            return
        #action type
        if obj.type == 'MESH':
            split = layout.split(factor=0.4, align = True)
            split.label(text = 'Data Type:')
            split.prop(obj.als, 'data_type', text ='')
        
        row = layout.row()        
        row.template_list("LAYERS_UL_list", "", context.object, "Anim_Layers", context.object.als, "layer_index", rows=2)  
        col = row.column(align=True)
        col.operator('anim.add_anim_layer', text="", icon = 'ADD')
        col.operator('anim.remove_anim_layer', text="", icon = 'REMOVE')
        col.separator()
        col.operator("anim.layer_move_up", text="", icon = 'TRIA_UP')
        col.operator("anim.layer_move_down", text="", icon = 'TRIA_DOWN')

        if not hasattr(anim_data, 'nla_tracks') or not len(obj.Anim_Layers) or obj.Anim_Layers[obj.als.layer_index].lock:
            return

        track = anim_data.nla_tracks[obj.als.layer_index]
            
        col=layout.column(align = True)
        row = col.row()   
        
        if not len(track.strips):
            return

        if len(track.strips[0].fcurves[0].keyframe_points) and not obj.Anim_Layers[obj.als.layer_index].influence_mute:
            row.prop(track.strips[0], 'influence', slider = True, text = 'Influence')
        else:
            row.prop(obj.Anim_Layers[obj.als.layer_index], 'influence', slider = True, text = 'Influence')
        icon = 'KEY_DEHLT' if track.strips[0].fcurves[0].mute else 'KEY_HLT'
        row.prop(obj.Anim_Layers[obj.als.layer_index],'influence_mute', invert_checkbox = True, expand = True, icon_only=True, icon = icon, icon_value = 1)
        row = layout.row()
        row.prop(obj.als, 'blend_type', text = 'Blend')
            
class ANIMLAYERS_PT_Ops(ANIMLAYERS_PT_Panel, bpy.types.Panel):
    bl_label = "Bake Operators"
    bl_idname = "ANIMLAYERS_PT_Ops"
    bl_parent_id = 'ANIMLAYERS_PT_List'
    #bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        obj = context.object
        if obj is None:
            return
        if not obj.als.turn_on:
            return
        anim_data = anim_data_type(obj)
        if not hasattr(anim_data, 'nla_tracks') or not len(obj.Anim_Layers) or obj.Anim_Layers[obj.als.layer_index].lock:
            return
        layout = self.layout              
        merge_layers = layout.column()
        #merge_layers.operator("anim.layers_merge_down", text="New Baked Layer", icon = 'NLA')
        merge_layers.operator("anim.layers_merge_down", text="Merge / Bake", icon = 'NLA_PUSHDOWN')
            
        duplicateanimlayer = layout.row(align=True)
        duplicateanimlayer.operator('anim.duplicate_anim_layer', text="Duplicate Layer", icon = 'SEQ_STRIP_DUPLICATE')
        icon = 'LINKED' if obj.als.linked else 'UNLINKED'
        duplicateanimlayer.prop(obj.als, 'linked', icon_only=True, icon = icon)

        extract = layout.row(align=True)
        extract.operator('anim.extract_selected_bones', text="Extract Selected Bones", icon = 'SELECT_SUBTRACT')
        markers = layout.row(align=True)
        markers.operator('anim.extract_markers', text="Extract Marked Keyframes", icon = 'MARKER_HLT')

class ANIMLAYERS_PT_Tools(ANIMLAYERS_PT_Panel, bpy.types.Panel):
    bl_label = "Tools & Settings"
    bl_idname = "ANIMLAYERS_PT_Tools"
    bl_parent_id = 'ANIMLAYERS_PT_List'
    #bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        obj = context.object
        if obj is None:
            return
        if not obj.als.turn_on:
            return
        if len(obj.Anim_Layers):
            if obj.Anim_Layers[obj.als.layer_index].lock:
                return
        
        layout = self.layout
        
        box = layout.box()
        box.label(text= 'Active Action:')
        anim_data = anim_data_type(obj)
        if anim_data is not None: 
            box.template_ID(anim_data, "action")
            row = box.row()
            split = row.split(factor=0.6, align = True)
            split.prop(obj.als, 'auto_rename', text = 'Auto Rename Layer')
            split.prop(obj.als, 'auto_blend')
        if not hasattr(anim_data, 'nla_tracks') or not len(obj.Anim_Layers):
            return
        box = layout.box()
        row = box.row()
        if obj.mode == 'POSE':
            row.prop(obj.als, 'only_selected_bones', text = 'Affect Only Selected Bones')#, icon = 'GROUP_BONE'

        
        row = box.row()
        row.operator("anim.bones_in_layer", text="Select Bones in Layer", icon = 'BONE_DATA')
        row = box.row()
        row.operator("anim.layer_reset_keyframes", text="Reset Key Layer ", icon = 'KEYFRAME')
        row = box.row()
        row.operator("anim.layer_cyclic_fcurves", text="Cyclic Fcurves", icon = 'FCURVE')
        row.operator("anim.layer_cyclic_remove", text="Remove Fcurves", icon = 'X')

        row = box.row()
        row.label(text= 'Keyframes From Multiple Layers:')
        row = box.row()
        split = row.split(factor=0.3, align = True)
        split.prop(obj.als, 'view_all_keyframes')
        
        if obj.als.view_all_keyframes:
            split.prop(obj.als, 'edit_all_keyframes')
            split.prop_menu_enum(obj.als, 'view_all_type')

classes = (ResetLayerKeyframes, LAYERS_UL_list, AddAnimLayer, ExtractSelection, ExtractMarkers, DuplicateAnimLayer, RemoveAnimLayer, CyclicFcurves, RemoveFcurves, MoveAnimLayerUp,
    MoveAnimLayerDown, SelectBonesInLayer, ANIMLAYERS_PT_List, ANIMLAYERS_PT_Ops, ANIMLAYERS_PT_Tools, ClearNLA)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.app.handlers.load_post.append(loadanimlayers)
    
    
def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    if loadanimlayers in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(loadanimlayers)
    if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)
    bpy.msgbus.clear_by_owner(bpy.context.scene)

       