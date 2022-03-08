import bpy
from bpy.app import driver_namespace
from . import anim_layers
from . import subscriptions

def frame_start_end(scene):
    if scene.use_preview_range:
        frame_start = scene.frame_preview_start
        frame_end = scene.frame_preview_end
    else:
        frame_start = scene.frame_start
        frame_end = scene.frame_end     
    return frame_start, frame_end

def smart_start_end(keyframes, frame_start, frame_end):
    '''add the first and last frame of the scene if necessery'''
    if not len(keyframes):
        return keyframes
    frames = [key.frame for key in keyframes]
    if min(frames) < frame_start:
        if frame_start not in frames:
            keystart = smartkey()
            keystart.startendkeys(frame_start)
            keyframes.append(keystart)      
        else:
            for keystart in keyframes:
                if keystart.frame == frame_start: 
                    keystart.startendkeys(frame_start)
                    break
        
    if max(frames) > frame_end:
        
        if frame_end not in frames:
            keyend = smartkey()
            keyend.startendkeys(frame_end)
            keyframes.append(keyend)     
        else:
            for keyend in reversed(keyframes):
                if keyend.frame == frame_end: 
                    keyend.startendkeys(frame_end)
                    break
    
    #remove keyframes that are outside of the timeline
    i = 0
    while i < len(keyframes):
        if keyframes[i].frame < frame_start or keyframes[i].frame > frame_end:
            keyframes.pop(i)
        else:
            i += 1
    keyframes.sort()
    
    return keyframes

def smart_cycle(keyframes, fcu, frame_start, frame_end):
    '''duplicates the smartkeys cycle'''

    for mod in fcu.modifiers:
        if mod.type != 'CYCLES' or mod.mute is True:
            continue
        fcu_range = int(fcu.range()[1] - fcu.range()[0])
        if not fcu_range:
            return keyframes
        if not mod.cycles_after and mod.mode_after != 'None':
            #if it's an iternal cycle then duplicate the keyframes until the scene frame end
            cycle_end_dup = int((frame_end - fcu.range()[1])/fcu_range)+2
            if mod.use_restricted_range and mod.frame_end < frame_end:
                cycle_end_dup = int((mod.frame_end - fcu.range()[1])/fcu_range)+2
        elif mod.mode_after != 'None':
            cycle_end_dup = mod.cycles_after
            if mod.use_restricted_range and mod.frame_end < (fcu.range()[1] + fcu_range * cycle_end_dup):
                cycle_end_dup = int((mod.frame_end - fcu.range()[1])/fcu_range)+2
        
        #copy the the right handle of the first keyframe to the last, and the left handle from the last keyframe to the first
        keyframes[-1].handle_right_type = keyframes[0].handle_right_type
        keyframes[0].handle_left_type = keyframes[0].handle_left_type
        keyframes[-1].handle_right = (keyframes[0].handle_right[0] + fcu_range, keyframes[0].handle_right[1])
        keyframes[0].handle_left = (keyframes[0].handle_left[0] + fcu_range, keyframes[0].handle_left[1])

        #duplicate the keys on the cycle after      
        keyframes_dup = []
        for key in keyframes[1:]:
            for i in range(cycle_end_dup):
                keydup = smartkey(key)
                keydup.frame += fcu_range*(i+1)
                #duplicate the tangents tuple values
                keydup.handle_left = (key.handle_left[0] + fcu_range*(i+1), key.handle_left[1])
                #if it's the last keyframe then the right handle get the value from the first keyframes
                keydup.handle_right = (key.handle_right[0] + fcu_range*(i+1), key.handle_right[1])
                
                if frame_end > key.frame > frame_start:
                    keyframes_dup.append(keydup)
        #if it's an iternal cycle then duplicate the keyframes before the cycle keyframes 
        if not mod.cycles_before and mod.mode_before != 'None':
            cycle_start_dup = int((fcu.range()[0] - frame_start) /fcu_range)+2
            if mod.use_restricted_range and mod.frame_start > frame_start:
                cycle_start_dup = int((fcu.range()[0]-mod.frame_start)/fcu_range)+2
        elif mod.mode_before != 'None':
            cycle_start_dup = mod.cycles_before
            if mod.use_restricted_range and mod.frame_start > (fcu.range()[0] + fcu_range * cycle_start_dup):
                cycle_start_dup = int((fcu.range()[0]-mod.frame_start)/fcu_range)+2

        #duplicate the keys on the cycle before            
        for key in keyframes[:-1]:
            for i in range(cycle_start_dup):
                keydup = smartkey(key)
                keydup.frame -= fcu_range*(i+1)
                #duplicate the tangents
                keydup.handle_left = (key.handle_left[0] - fcu_range*(i+1), key.handle_left[1])
                keydup.handle_right = (key.handle_right[0] - fcu_range*(i+1), key.handle_right[1])
                if frame_end > key.frame > frame_start:
                    keyframes_dup.append(keydup)
                 
        #merge the keyframes from the cycle with the original keyframes
        keyframes.extend(keyframes_dup)
        keyframes.sort()
        
        if mod.use_restricted_range:
            keyframes = smart_start_end(keyframes, mod.frame_start, mod.frame_end)
            keyframes = smart_start_end(keyframes, mod.frame_start+1, mod.frame_end-1)
        else:
            keyframes = smart_start_end(keyframes, frame_start, frame_end)
    return keyframes
                    
def smart_bake(self, context):
    obj = context.object
    frame_start, frame_end = frame_start_end(context.scene)
    fcu_smartkeys = {}
    anim_data = anim_layers.anim_data_type(obj)
    cyclic_dup = False
    cyclic_track = False
    for track in anim_data.nla_tracks[:-1]:
        if track.mute:
            continue
        if len(track.strips) != 1 or track.strips[0].action is None:
            continue
        for fcu in track.strips[0].action.fcurves:
            if not fcu.is_valid or fcu.mute or selected_bones_filter(obj, fcu.data_path):
                continue
            smartkeys = []
            #duplicate all the keyframes into a new keyframes class duplicate
            for key in fcu.keyframe_points:
                if key not in smartkeys:
                    smartkeys.append(smartkey(key))
            
            #if the list of keyframes exists in a different track list then MERGE them
            if (fcu.data_path, fcu.array_index) in fcu_smartkeys:
                smartkeys = list(set(fcu_smartkeys[(fcu.data_path, fcu.array_index)]+smartkeys))
                smartkeys.sort()

            
            if len(fcu.modifiers) and obj.als.mergefcurves and not cyclic_track: #and obj.als.layer_index != i
                smartkeys = smart_cycle(smartkeys, fcu, frame_start, frame_end)
                cyclic_dup = True
                
            fcu_smartkeys.update({(fcu.data_path, fcu.array_index):smartkeys})

        cyclic_track = cyclic_dup
    #add inbetweens
    for fcu, smartkeys in fcu_smartkeys.items():
        smartkeys = smart_start_end(smartkeys, frame_start, frame_end)
        smartkeys = add_inbetween(smartkeys)

    return fcu_smartkeys

def add_inbetween(smartkeys):
    i = 0
    while i < len(smartkeys)-1:
        if smartkeys[i].inbetween:
            continue
        key1 = smartkey()
        key1.frame = smartkeys[i].frame + (smartkeys[i+1].frame - smartkeys[i].frame)*1/3
        key1.inbetween = True
        
        key2 = smartkey()
        key2.frame = smartkeys[i].frame + (smartkeys[i+1].frame - smartkeys[i].frame)*2/3
        key2.inbetween = True
        smartkeys.insert(i+1, key1)
        smartkeys.insert(i+2, key2)
        i += 3 

    return smartkeys

class smartkey:
    def __init__(self, key = None):
        if not key:
            return
        if hasattr(key, 'co'):
            self.frame = key.co[0]
        elif hasattr(key, 'frame'):
            self.frame = key.frame
        self.interpolation = key.interpolation
        self.handle_left_type = key.handle_left_type
        self.handle_right_type = key.handle_right_type
        self.handle_left = key.handle_left
        self.handle_right = key.handle_right
        self.easing = key.easing
        self.inbetween = False

    def startendkeys(self, frame):
        self.frame = frame
        self.interpolation = 'BEZIER'
        self.handle_left_type = 'VECTOR'
        self.handle_right_type = 'VECTOR'
        self.inbetween = False

    def __lt__(self, other):
        return self.frame < other.frame

    def __hash__(self):
        return hash(self.frame)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.frame == other.frame

def mute_unbaked_layers(layer_index, nla_tracks, additive):
    obj = bpy.context.object
    #a list to record which layers that are not merged were muted
    mute_rec = [] 
    #mute the layers that are not going to be baked
    if obj.als.direction == 'ALL':
        return mute_rec

    for index, track in enumerate(nla_tracks[:-1]):
        #if running into a replace layer during additive bake then exclude the rest of the layers from the bake
        if track.mute:
            mute_rec.append(track)
            continue
        if additive and track.strips[0].blend_type == 'REPLACE' and index >= layer_index:
            layer_index = len(nla_tracks)-1
        if obj.als.direction == 'DOWN' and index > layer_index:
            track.mute = True
            track.select = False
        if obj.als.direction == 'UP' and index < layer_index:
            track.mute = True
            track.select = False
      
    return mute_rec

def mute_modifiers(context, obj, nla_tracks, frame_start):
    #disable modifiers if merge fcurves is false
    modifier_rec = []
    extrapolations = []
    for track in nla_tracks:
        if len(track.strips) != 1 or track.strips[0].action is None:
            continue
        for fcu in track.strips[0].action.fcurves:
            if selected_bones_filter(obj, fcu.data_path):
                continue
            if fcu.extrapolation == 'LINEAR':
                extrapolations.append((fcu.data_path, fcu.array_index))
            if fcu.lock:
                fcu.lock = False
            if fcu.group is not None:
                if fcu.group.lock:
                    fcu.group.lock = False
            if not fcu.is_valid:
                continue
            if len(fcu.modifiers) and not obj.als.mergefcurves:
                for mod in fcu.modifiers:
                    if mod.mute == False:
                        modifier_rec.append(mod)
                        mod.mute = True                          

    return modifier_rec, extrapolations

def unmute_modifiers(obj, nla_tracks, modifier_rec):
    #Turn on fcurve modifiers if merge fcurves is false
    for track in nla_tracks:
        for fcu in track.strips[0].action.fcurves:
            if not fcu.is_valid or selected_bones_filter(obj, fcu.data_path):
                continue
            if not len(fcu.modifiers):
                continue
            for mod in fcu.modifiers:
                if mod in modifier_rec:
                    mod.mute = False
                elif obj.als.mergefcurves and track == nla_tracks[obj.als.layer_index]:
                    mod.mute = True

def invisible_layers(obj, b_layers):
    #Store the current invisible layer bones and make them visible for baking
    layers_rec = []
    for i in range(len(b_layers)):
        if b_layers[i] == False:
            layers_rec.append(i)
            b_layers[i] = True
    return layers_rec

def select_keyframed_bones(self, context, obj):
    #Select all keyframed bones in layers if not only selected
    if obj.als.onlyselected:
        return
    if obj.mode != 'POSE':
        bpy.ops.object.posemode_toggle()
    bpy.ops.pose.select_all(action='DESELECT')
    for i in range(0, obj.als.layer_index+1):
        obj.als.layer_index = i
        anim_layers.select_layer_bones(self, context)

def mute_constraints(obj):
    #Mute constraints if are not cleared during bake
    constraint_rec = [] 
    if obj.als.clearconstraints:
        return constraint_rec
    for bone in bpy.context.selected_pose_bones:
        for constraint in bone.constraints:
            if constraint.mute == False:
                constraint_rec.append(constraint)
                constraint.mute = True
    return constraint_rec

def smartbake_apply(self, obj, nla_tracks, fcu_keys, extrapolations):
    #smart bake - delete unnecessery keyframes:
    transform_types = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']
    strip = nla_tracks[obj.als.layer_index].strips[0]
    action_range = int(strip.action.frame_range[1] + 1 -  strip.action.frame_range[0])  
    for fcu in strip.action.fcurves:
        if not fcu.is_valid:
            continue
        if selected_bones_filter(obj, fcu.data_path):
            continue
        fcu_key = (fcu.data_path, fcu.array_index)
        if fcu_key not in fcu_keys.keys():
            strip.action.fcurves.remove(fcu)
            continue
        #get all the frames of the smart keys
        smartkeys = fcu_keys[fcu_key]
        smart_frames = [key.frame for key in smartkeys if not key.inbetween]
        
        #Get all the inbetween values
        for smartkey in smartkeys:
            if smartkey.inbetween:
                smartkey.value = round(fcu.evaluate(smartkey.frame), 4)

        #add keyframes that are missing from the bake but included in the smart bake
        if len(fcu.keyframe_points) < action_range :
            #get all the frames of the baked keyframes
            key_frames = [key.co[0] for key in fcu.keyframe_points]
            for smart_key in smartkeys:
                if smart_key.frame > strip.action.frame_range[1]:
                    break
                if smart_key.inbetween:
                    continue
                if smart_key.frame not in key_frames:
                    value = fcu.evaluate(smart_key.frame)
                    fcu.keyframe_points.add(1)
                    fcu.keyframe_points[-1].co = (smart_key.frame, value)
                    fcu.update()        
                    
        #remove unnecessery keyframes
        for i in range(int(strip.action.frame_range[0]),int(strip.action.frame_range[1]+1)):
            if i in smart_frames:
                #get the index of the smart key based on the smart frames + interpolations
                smart_index = (smart_frames.index(i)+1)*3-3

                #if key was founded add the interpolation and handles
                for key in fcu.keyframe_points:
                    if key.co[0] == i:
                        key.co[1] = round(key.co[1], 4)
                        key.interpolation = smartkeys[smart_index].interpolation
                        # key.handle_left_type = smartkeys[smart_index].handle_left_type
                        # key.handle_right_type = smartkeys[smart_index].handle_right_type
                        key.handle_left_type = 'AUTO_CLAMPED' if smartkeys[smart_index].handle_left_type != 'VECTOR' else 'VECTOR'
                        key.handle_right_type = 'AUTO_CLAMPED' if smartkeys[smart_index].handle_right_type != 'VECTOR' else 'VECTOR'
                        break
            #delete the keys that are not in the list
            else:
                if fcu.data_path.split(".")[-1] in transform_types:
                    obj.keyframe_delete(fcu_key[0],index = fcu_key[1], frame = i)
                else:
                    try:
                        obj.keyframe_delete(fcu_key[0], frame = i)
                    except TypeError:
                        pass
        #if self.handles == 'RECALC':
        add_interpolations(fcu, smartkeys)
        if (fcu.data_path, fcu.array_index) in extrapolations:
            fcu.extrapolation = 'LINEAR'
        fcu.update()

def armature_restore(obj, b_layers, layers_rec, constraint_rec):
    if obj.type != 'ARMATURE':
        return
    #Turn off previous invisible bone layers
    for i in range(len(b_layers)):
        if i in layers_rec:
            b_layers[i] = False   
                    
    #Turn on constraints
    if not obj.als.clearconstraints:
        for constraint in constraint_rec:
            constraint.mute = False

def attr_default(obj, fcu_key):

    #check if the fcurve source belongs to a bone or obj
    if  fcu_key[0][:10] == 'pose.bones':
        transform = fcu_key[0].split('.')[-1]
        attr = fcu_key[0].split('"')[-2]
        bone = fcu_key[0].split('"')[1]
        source = obj.pose.bones[bone]   
    else:
        source = obj
        transform = fcu_key[0]
    
    #check when it's transform property of Blender
    if transform in source.bl_rna.properties.keys():
        if hasattr(source.bl_rna.properties[transform], 'default_array'):
            if len(source.bl_rna.properties[transform].default_array) > fcu_key[1]:
                attrvalue = source.bl_rna.properties[transform].default_array[fcu_key[1]]
                return attrvalue
        #else:
        attrvalue = source.bl_rna.properties[transform].default
        return attrvalue

    #check when it's a custom property
    if '_RNA_UI' in source.keys() and attr in source.keys():
        if attr in source['_RNA_UI'].keys():
            if 'default' in source['_RNA_UI'][attr].keys():
                attrvalue = source['_RNA_UI'][attr]['default']
                return attrvalue

    return 0

def selected_bones_filter(obj, fcu_data_path):
    if not obj.als.onlyselected:
        return False
    if obj.mode != 'POSE':
        return True
    transform_types = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']
    #filter selected bones if option is turned on
    bones = [bone.path_from_id() for bone in bpy.context.selected_pose_bones]
    if fcu_data_path.split('].')[0]+']' not in bones and fcu_data_path not in transform_types:
        return True

def AL_bake(self, frame_start, frame_end, nla_tracks, fcu_keys, additive, baked_layer = None):
    #iterate through all the frames
    obj = bpy.context.object
    if obj is None:
        return
    anim_data = anim_layers.anim_data_type(obj)
    if obj.als.operator == 'MERGE' and obj.als.onlyselected and not additive:
        baked_action = anim_data.action.copy()
    else:
        baked_action = bpy.data.actions.new('Baked action')
    baked_action.id_root = obj.als.data_type
    blend_types = {'ADD' : '+', 'SUBTRACT' : '-', 'MULTIPLY' : '*'}
    for fcu_key, smartkeys in fcu_keys.items():
        if selected_bones_filter(obj, fcu_key[0]):
            continue
        smart_frames = [key.frame for key in smartkeys] # if not keyframe.inbetween
        mod_list = []
        modifier_rec = []
        attrvalue = None
        if not smart_frames:
            continue
        #find or create the fcurve in the new action
        baked_fcu = baked_action.fcurves.find(fcu_key[0], index = fcu_key[1])
        if baked_fcu is None:
            baked_fcu = baked_action.fcurves.new(fcu_key[0], index = fcu_key[1])
        else:
            baked_action.fcurves.remove(baked_fcu)
            baked_fcu = baked_action.fcurves.new(fcu_key[0], index = fcu_key[1])
        baked_fcu.color_mode = 'AUTO_RGB'
        #select smart bake frame range or every frame in the range       
        if obj.als.smartbake:
            frame_range = smart_frames
        else:
            frame_range = range(frame_start, frame_end+1)

        for frame in frame_range:
            #if frame not in smart_frames and obj.als.smartbake:
            #    continue
            if obj.als.smartbake and (frame > max(smart_frames) or frame < min(smart_frames)):
                continue
            evaluate = 0
            layers_count = 0

            #Evaluate the value of the current frame from all the unmuted tracks
            for track in nla_tracks[:-1]:
                if track.mute or track == baked_layer:
                    continue
                blend_type = track.strips[0].blend_type
                if blend_type =='COMBINE':
                    continue
                fcu = track.strips[0].action.fcurves.find(fcu_key[0], index = fcu_key[1])

                #get the influence value either from the attribute or the fcurve
                if not track.strips[0].fcurves[0].mute and len(track.strips[0].fcurves[0].keyframe_points):
                    influence = track.strips[0].fcurves[0].evaluate(frame)
                else:
                    influence = track.strips[0].influence

                #If there is no scale value on the replace layer, then evaluate the value directly from the channel attribue
                if (fcu is None or fcu.mute) and track.strips[0].blend_type == 'REPLACE' and not evaluate:
                    attrvalue = attr_default(obj, fcu_key)
                    if isinstance(attrvalue, str):
                        continue
                    if attrvalue is not None:
                        evaluate = evaluate * (1 - influence) + attrvalue * influence
                        continue
                    
                if fcu is None or fcu.mute:
                    continue
                
                if hasattr(fcu, 'group'):
                    group = fcu.group.name if fcu.group is not None else None    
                else:
                    group = None

                #copy and append Modifiers into mod_list. Mute them if turned on
                if len(fcu.modifiers) and not obj.als.mergefcurves and not mod_list:
                    for mod in fcu.modifiers:
                        mod_list = anim_layers.copy_modifiers(mod, mod_list)
                        #turn off modifier after copying it and append it
                        if mod.mute == False:
                            modifier_rec.append(mod)
                            mod.mute = True

                ###EVALUATION###
                if blend_type =='REPLACE':  
                    evaluate = evaluate * (1 - influence) + fcu.evaluate(frame) * influence 
                else:
                    #evaluate += fcu.evaluate(frame) * influence
                    evaluate = eval(str(evaluate) + blend_types[track.strips[0].blend_type] + str(fcu.evaluate(frame)) + '*' + str(influence))

                
                extrapolation = True if fcu.extrapolation == 'LINEAR' else False
                layers_count += 1

                #UNMUTE the original fcurve MODIFIERS if necessery. Do it once in the end of smartkeys instead of every frame
                if not len(fcu.modifiers) or frame != sorted(smart_frames)[-1]:
                    continue
                for mod in fcu.modifiers:
                    if mod in modifier_rec:
                        mod.mute = False
                    elif obj.als.mergefcurves and track == nla_tracks[obj.als.layer_index]:
                        mod.mute = True
            
            #add the final result to the smart key and a list
            if obj.als.smartbake:
                smartkey = smartkeys[smart_frames.index(frame)]
                smartkey.value = evaluate
            
                #add the fcurve evaluation to the current action
                if not smartkey.inbetween:
                    baked_fcu.keyframe_points.add(1)
                    keyframe = baked_fcu.keyframe_points[-1]
                    keyframe.co = (frame, evaluate)
            else: #if rendering on every frame
                baked_fcu.keyframe_points.add(1)
                keyframe = baked_fcu.keyframe_points[-1]
                keyframe.co = (frame, evaluate)

        if baked_fcu.group is None and group is not None:
            if group in baked_action.groups.keys():
                baked_fcu.group = baked_action.groups[group]
            else:
                baked_fcu.group = baked_action.groups.new(group)
        if extrapolation and obj.als.smartbake:
            baked_fcu.extrapolation = 'LINEAR'
        baked_fcu.update()
       
        if obj.als.smartbake:
            baked_fcu.update()
            #if self.handles == 'RECALC':
            add_interpolations(baked_fcu, smartkeys, layers_count)

        #paste the modifiers to the new baked fcurve
        if len(mod_list):
            anim_layers.paste_modifiers(baked_fcu, mod_list)
    return baked_action
        
def add_interpolations(baked_fcu, smartkeys, layers_count = 0):
    '''Add the interpolation or control points between every two smartkeys'''

    baked_keys = baked_fcu.keyframe_points
    keys = [key for key in smartkeys if not key.inbetween]
    
    #the index for the inbetweens
    P1index = 1
    P2index = 2
    for i, key in enumerate(keys[:-1]):
        skip = False

        #if the fcurve was counted only once, then just copy the old handle values instead of recalculating
        if layers_count == 1 and key != keys[0]:# and i < len(keys) - 3:
            baked_keys[i].handle_left_type = key.handle_left_type
            baked_keys[i].handle_right_type = key.handle_right_type
            baked_keys[i].handle_right = key.handle_right
            baked_keys[i].handle_left = key.handle_left
            P1index += 3
            P2index += 3
            skip = True

        if key.interpolation != 'BEZIER':
            baked_keys[i].interpolation = key.interpolation
            baked_keys[i].easing = key.easing
            P1index += 3
            P2index += 3
            baked_fcu.update() 
            skip = True

        if skip:
            continue
        
        # #Exit because Handles applied already in one keyframe before the last
        # if keys[-1] == key:
        #     baked_fcu.update() 
        #     break
         
        #skip if value not found in smartkey (bug that need to be solved)
        if not hasattr(smartkeys[P1index], 'value') or not hasattr(smartkeys[P2index], 'value'):
            baked_keys[i].handle_right_type = key.handle_left_type
            baked_keys[i+1].handle_left_type = key.handle_right_type
            print(baked_fcu.data_path, 'missing smartkey value', baked_keys[i])
            P1index += 3
            P2index += 3
            continue
        
        P0 = baked_keys[i].co[1]
        P3 = baked_keys[i+1].co[1]

        P1 = smartkeys[P1index].value
        P2 = smartkeys[P2index].value

        cp1 = (1/6)*( -5*P0 + 18*P1 - 9*P2 + 2*P3)
        cp2 = (1/6)*(  2*P0 -  9*P1 +18*P2 - 5*P3)

        baked_keys[i].handle_right_type = 'FREE'
        baked_keys[i+1].handle_left_type = 'FREE'

        baked_keys[i].handle_right = (smartkeys[P1index].frame, cp1)
        baked_keys[i+1].handle_left = (smartkeys[P2index].frame, cp2)
        
        #iterate through the inbetween smartkeys
        P1index += 3
        P2index += 3

        baked_fcu.update() 
    
        #add in-betweener
        #frame_range / (frame_range * factor) 
 
    
class MergeAnimLayerDown(bpy.types.Operator):
    """Merge and bake the layers from the current selected layer down to the base"""
    bl_idname = "anim.layers_merge_down"
    bl_label = "Merge_Layers_Down"
    bl_options = {'REGISTER', 'UNDO'}
    
    #limited property of diretion for blender's bake
    direction: bpy.props.EnumProperty(name = '', description="Select direction of merge", items = [('DOWN', 'Down', 'Merge downwards','TRIA_DOWN', 0), ('ALL', 'All', 'Merge all layers', 1)])
    # handles: bpy.props.EnumProperty(name = '', description="Recalculate bezier handles from the new baked curves or apply auto clamped handles", 
    #     items = [('RECALC', 'Recalculate', '"Recalculate bezier handles from new baked curves','CURVE_BEZCURVE', 0), ('AUTO', 'Auto Clamped', 'Apply Auto Clamped Handles','HANDLE_AUTOCLAMPED', 1)])

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width = 200)

    def draw(self, context):
        obj = context.object
        layout = self.layout
        box = layout.box()
        if obj.als.data_type == 'OBJECT':
            split = box.split(factor=0.5, align = True)
            split.label(text = 'Bake Type :')
            split.prop(obj.als, 'baketype')
        split = box.split(factor=0.5, align = True)
        split.label(text = 'Bake Operator :')
        split.prop(obj.als, 'operator')
        split = box.split(factor=0.5, align = True)
        split.label(text = 'Bake Direction :')
        if obj.als.baketype == 'BLENDER':
            split.prop(self, 'direction')
        else:
            split.prop(obj.als, 'direction')
        if obj.als.baketype == 'BLENDER':
            box.prop(obj.als, 'clearconstraints')
        box.prop(obj.als, 'mergefcurves')
        split = box.split(factor=0.5, align = True)
        split.prop(obj.als, 'smartbake')
        # if obj.als.smartbake:
        #     split.prop(self, 'handles')
            #split.label(text = 'Bezier handles')
        if obj.mode == 'POSE':
            box.prop(obj.als, 'onlyselected')

    def execute(self, context):
        obj = bpy.context.object
        if obj is None:
            return {'CANCELLED'}
        anim_data = anim_layers.anim_data_type(obj)
        nla_tracks = anim_data.nla_tracks
        
        if obj.als.direction == 'DOWN' and not obj.als.layer_index:
            return {'CANCELLED'}

        #disable baking up from Blender's bake
        if obj.als.baketype =='BLENDER':
            obj.als.direction = self.direction
        if obj.als.direction == 'UP' and obj.als.layer_index == len(nla_tracks)-2:
            return {'CANCELLED'}
        
        if subscriptions.check_handler in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.remove(subscriptions.check_handler)

        #define the start and end frame of the bake, according to scene or preview length 
        frame_start, frame_end = frame_start_end(bpy.context.scene)
        obj.als.view_all_keyframes = False                     

        layer_index = obj.als.layer_index
        
        #define if the new baked layer is going to be additive or replace
        if obj.als.direction == 'UP' and nla_tracks[obj.als.layer_index].strips[0].blend_type == 'ADD' and obj.als.baketype == 'AL':
            additive = True
            blend = 'ADD'
        else:
            additive = False
            blend = 'REPLACE'
            
        fcu_keys = smart_bake(obj, context)

        if obj.als.operator == 'MERGE':
            if obj.als.direction == 'DOWN':     
                obj.als.layer_index = 0
            baked_layer = None
            action_name = anim_data.nla_tracks[obj.als.layer_index].strips[0].action.name        

        #if baking to a new layer then setup the new index and layer
        elif obj.als.operator == 'NEW':
            blendings = [track.strips[0].blend_type for track in nla_tracks[layer_index:-1] if len(track.strips) == 1]
            if  obj.als.direction == 'UP' and additive and 'REPLACE' in blendings:
                obj.als.layer_index =  layer_index + blendings.index('REPLACE') - 1
            elif obj.als.direction == 'UP' or obj.als.direction == 'ALL':
                obj.als.layer_index = len(obj.Anim_Layers)-1
            layer_names = [layer.name for layer in obj.Anim_Layers]
            baked_layer = anim_layers.add_animlayer(layer_name = anim_layers.unique_name(layer_names, 'Baked_Layer') , duplicate = False, index = obj.als.layer_index, blend_type = blend)
            anim_layers.register_layers(obj, nla_tracks)

            obj.als.layer_index += 1

        mute_rec = mute_unbaked_layers(layer_index, nla_tracks, additive)
        
        #use internal bake
        if obj.als.baketype =='BLENDER':
            modifier_rec, extrapolations = mute_modifiers(context, obj, nla_tracks, frame_start)
            if obj.als.smartbake and not obj.als.mergefcurves:
                #apply the last frame of the smart bake instead of the whole action when it has a smaller value
                smart_end = max(([value.frame for fcu_values in fcu_keys.values() for value in fcu_values]))
                if smart_end < frame_end : frame_end = smart_end
            if obj.type == 'ARMATURE':
                b_layers = obj.data.layers
                layers_rec = invisible_layers(obj, b_layers)
                
                select_keyframed_bones(self, context, obj)
                        
                constraint_rec = mute_constraints(obj)
            if obj.als.onlyselected:
                bake_type = {'POSE'}
            else:
                bake_type = {'OBJECT', 'POSE'}
            bpy.ops.nla.bake(frame_start = frame_start, frame_end = frame_end, only_selected = True, visual_keying=True, clear_constraints=obj.als.clearconstraints, use_current_action=True, bake_types = bake_type)
            anim_data.action.fcurves.update()
            if obj.als.smartbake:
                smartbake_apply(self, obj, nla_tracks, fcu_keys, extrapolations)
            if obj.type == 'ARMATURE':
                armature_restore(obj, b_layers, layers_rec, constraint_rec)
            unmute_modifiers(obj, nla_tracks, modifier_rec)

        else: #use anim layers bake
            action = AL_bake(self, frame_start, frame_end, nla_tracks, fcu_keys, additive, baked_layer)
            #anim_layers.action = action
            nla_tracks[obj.als.layer_index].strips[0].action = action

        #removing layers after merge
        if obj.als.operator == 'MERGE':
            nla_tracks[obj.als.layer_index].strips[0].blend_type = blend
            if obj.als.baketype == 'AL':
                #Rename the old action with a number
                bpy.data.actions[action_name].use_fake_user = False
                bpy.data.actions[action_name].name = anim_layers.unique_name(bpy.data.actions, action_name)
                #Rename the current action to the old action
                action.name = action_name

            #delete the baked layers except for the base layer
            if obj.als.direction == 'DOWN':
                while layer_index  > 0:
                    nla_tracks.remove(nla_tracks[layer_index])
                    layer_index -= 1
                
            if obj.als.direction == 'UP':
                layer_index += 1
                while layer_index < len(nla_tracks)-1:
                    if additive and nla_tracks[layer_index].strips[0].blend_type == 'REPLACE':
                        break
                    nla_tracks.remove(nla_tracks[layer_index])
            
            if obj.als.direction == 'ALL':
                obj.als.layer_index = 0
                index = 0
                merged_track = nla_tracks[layer_index]
                while len(nla_tracks)-1 > 1:
                    if nla_tracks[index] != merged_track:
                        nla_tracks.remove(nla_tracks[index])
                    else:
                        index += 1

            #reset influence of merged layer
            strip = nla_tracks[obj.als.layer_index].strips[0]
            while len(strip.fcurves[0].keyframe_points):
                strip.fcurves[0].keyframe_points.remove(strip.fcurves[0].keyframe_points[0])
            strip.influence = 1
            
        #turn the tracks back on if necessery
        if obj.als.direction != 'ALL':
            for track in nla_tracks:
                if track in mute_rec:
                    track.mute = True
                else:
                    track.mute = False

        anim_layers.register_layers(obj, nla_tracks)

        if subscriptions.check_handler not in bpy.app.handlers.depsgraph_update_pre:
            bpy.app.handlers.depsgraph_update_pre.append(subscriptions.check_handler)
                   
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MergeAnimLayerDown)

def unregister():
    bpy.utils.unregister_class(MergeAnimLayerDown)
