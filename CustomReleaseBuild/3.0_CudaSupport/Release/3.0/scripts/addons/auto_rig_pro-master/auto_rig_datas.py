import bpy
import mathutils
from mathutils import *

# ARMS
#   Fingers
#     thumb
thumb_ref_dict = {'thumb1':'thumb1_ref', 'thumb2':'thumb2_ref', 'thumb3':'thumb3_ref'}
thumb_ref_list = [j for i, j in thumb_ref_dict.items()]

thumb_control_dict = {'base':'c_thumb1_base', '1':'c_thumb1', '2':'c_thumb2', '3':'c_thumb3'}
thumb_control_list = [j for i, j in thumb_control_dict.items()]

thumb_intern_dict = {'base':'thumb1', 'bend_all':'thumb_bend_all', 'rot1':'c_thumb1_rot', 'rot2':'c_thumb2_rot', 'rot3':'c_thumb3_rot'}
thumb_intern_list = [j for i, j in thumb_intern_dict.items()]

#    index
index_ref_dict = {'index_meta':'index1_base_ref', 'index1':'index1_ref', 'index2':'index2_ref', 'index3':'index3_ref'}
index_ref_list = [j for i, j in index_ref_dict.items()]

index_control_dict = {i: j.replace('thumb', 'index') for i, j in thumb_control_dict.items()}
index_control_list = [j for i, j in index_control_dict.items()]

index_intern_dict = {i: j.replace('thumb','index') for i, j in thumb_intern_dict.items()}
index_intern_list = [j for i, j in index_intern_dict.items()]

#    middle
middle_ref_dict = {'middle_meta':'middle1_base_ref', 'middle1':'middle1_ref', 'middle2':'middle2_ref', 'middle3':'middle3_ref'}
middle_ref_list = [j for i, j in middle_ref_dict.items()]

middle_control_dict = {i: j.replace('thumb', 'middle') for i, j in thumb_control_dict.items()}
middle_control_list = [j for i, j in middle_control_dict.items()]

middle_intern_dict = {i: j.replace('thumb','middle') for i, j in thumb_intern_dict.items()}
middle_intern_list = [j for i, j in middle_intern_dict.items()]

#    ring
ring_ref_dict = {'ring_meta':'ring1_base_ref', 'ring1':'ring1_ref', 'ring2':'ring2_ref', 'ring3':'ring3_ref'}
ring_ref_list = [j for i, j in ring_ref_dict.items()]

ring_control_dict = {i: j.replace('thumb', 'ring') for i, j in thumb_control_dict.items()}
ring_control_list = [j for i, j in ring_control_dict.items()]

ring_intern_dict = {i: j.replace('thumb','ring') for i, j in thumb_intern_dict.items()}
ring_intern_list = [j for i, j in ring_intern_dict.items()]

#    pinky
pinky_ref_dict = {'pinky_meta':'pinky1_base_ref', 'pinky1':'pinky1_ref', 'pinky2':'pinky2_ref', 'pinky3':'pinky3_ref'}
pinky_ref_list = [j for i, j in pinky_ref_dict.items()]

pinky_control_dict = {i: j.replace('thumb', 'pinky') for i, j in thumb_control_dict.items()}
pinky_control_list = [j for i, j in pinky_control_dict.items()]

pinky_intern_dict = {i: j.replace('thumb','pinky') for i, j in thumb_intern_dict.items()}
pinky_intern_list = [j for i, j in pinky_intern_dict.items()]


fingers_control = thumb_control_list + index_control_list + middle_control_list + ring_control_list + pinky_control_list
fingers_intern = thumb_intern_list + index_intern_list + middle_intern_list + ring_intern_list + pinky_intern_list

#     ik
fingers_control_ik = []
for finger_type in ["thumb", "index", "middle", "ring", "pinky"]:
    for fi in range(1, 4):
        fingers_control_ik.append("c_"+finger_type+str(fi)+"_ik")
    
    fingers_control_ik.append("c_"+finger_type+"_ik")# target
    fingers_control_ik.append("c_"+finger_type+"_ik2")
    fingers_control_ik.append("c_"+finger_type+"_pole")# pole
    

#   Arms
arm_bones_dict = {
    'shoulder':{'control':'c_shoulder', 'deform':'shoulder', 'track_pole':'shoulder_track_pole', 'pole':'shoulder_pole'},
    'arm':{'base':'arm', 'twist':'arm_twist', 'twist_twk':'arm_twist_twk', 'control_twist':'c_arm_twist_offset', 'stretch':'arm_stretch', 'control_fk':'c_arm_fk', 'fk':'arm_fk', 'ik':'arm_ik', 'control_ik':'c_arm_ik', 'ik_scale_fix':'arm_ik_nostr_scale_fix', 'ik_nostr':'arm_ik_nostr', 'secondary_00':'c_shoulder_bend','secondary_01':'c_arm_bend'},
    'forearm':{'base':'forearm', 'control_fk':'c_forearm_fk', 'fk':'forearm_fk', 'ik':'forearm_ik', 'ik_nostr':'forearm_ik_nostr', 'stretch':'forearm_stretch', 'twist':'forearm_twist', 'secondary_00':'c_elbow_bend', 'secondary_01':'c_forearm_bend', 'secondary_02':'c_wrist_bend'},
    'hand':{'deform':'hand', 'control_fk':'c_hand_fk', 'control_ik':'c_hand_ik', 'fk_scale_fix':'c_hand_fk_scale_fix', 'rot_twist':'hand_rot_twist', 'secondary_00':'hand_bend'},
    'prepole':'arm_fk_pre_pole',
    'fk_pole':'arm_fk_pole',
    'control_pin':'c_stretch_arm_pin',
    'control_stretch':'c_stretch_arm',
    'control_pole_ik': 'c_arms_pole'}
    
arm_bones = []
for i, j in arm_bones_dict.items():
    if type(j) is dict:
        for k, l in j.items():
            arm_bones.append(l)            
    else:
        arm_bones.append(j)
        
# add fingers
arm_bones = arm_bones + fingers_control + fingers_intern

arm_ref_dict = {'shoulder':'shoulder_ref', 'arm':'arm_ref', 'forearm':'forearm_ref', 'hand':'hand_ref', **thumb_ref_dict, **index_ref_dict, **middle_ref_dict, **ring_ref_dict, **pinky_ref_dict}

arm_ref_list = [j for i, j in arm_ref_dict.items()]

arm_bones_rig_add = [arm_bones_dict['arm']['secondary_00'], arm_bones_dict['arm']['secondary_01'], arm_bones_dict['forearm']['secondary_00'], arm_bones_dict['forearm']['secondary_01'], arm_bones_dict['forearm']['secondary_02'], arm_bones_dict['hand']['secondary_00']]

arm_deform = [arm_bones_dict['shoulder']['deform'], arm_bones_dict['arm']['control_twist'], arm_bones_dict['arm']['stretch'], arm_bones_dict['forearm']['twist'], arm_bones_dict['forearm']['stretch'], arm_bones_dict['hand']['deform']]

arm_control = [arm_bones_dict['hand']['control_ik'], arm_bones_dict['hand']['control_fk'], arm_bones_dict['arm']['control_fk'], arm_bones_dict['arm']['control_ik'], arm_bones_dict['forearm']['control_fk'], arm_bones_dict['shoulder']['control'], arm_bones_dict['arm']['control_twist'], arm_bones_dict['control_pole_ik'], arm_bones_dict['arm']['secondary_00'], arm_bones_dict['arm']['secondary_01'], arm_bones_dict['forearm']['secondary_00'], arm_bones_dict['forearm']['secondary_01'], arm_bones_dict['forearm']['secondary_02'], arm_bones_dict['control_stretch'], arm_bones_dict['control_pin']]

arm_bendy_dict = {'arm':'arm_bendy', 'forearm':'forearm_bendy'}


# LEGS
#   toes
toes_thumb_ref_dict = {'toes_thumb1':'toes_thumb1_ref', 'toes_thumb2':'toes_thumb2_ref'}
toes_thumb_ref_list = [j for i, j in toes_thumb_ref_dict.items()]
toes_thumb_control_dict = {'1': 'c_toes_thumb1', '2':'c_toes_thumb2'}
toes_thumb_control_list = [j for i, j in toes_thumb_control_dict.items()]

toes_index_ref_dict = {'toes_index1':'toes_index1_ref', 'toes_index2':'toes_index2_ref', 'toes_index3':'toes_index3_ref'}
toes_index_ref_list = [j for i, j in toes_index_ref_dict.items()]
toes_index_control_dict = {'1': 'c_toes_index1', '2':'c_toes_index2', '3':'c_toes_index3'}
toes_index_control_list = [j for i, j in toes_index_control_dict.items()]

toes_middle_ref_dict = {'toes_middle1':'toes_middle1_ref', 'toes_middle2':'toes_middle2_ref', 'toes_middle3':'toes_middle3_ref'}
toes_middle_ref_list = [j for i, j in toes_middle_ref_dict.items()]
toes_middle_control_dict = {i: j.replace('index','middle') for i, j in toes_index_control_dict.items()}
toes_middle_control_list =  [j for i, j in toes_middle_control_dict.items()]

toes_ring_ref_dict = {'toes_ring1':'toes_ring1_ref', 'toes_ring2':'toes_ring2_ref', 'toes_ring3':'toes_ring3_ref'}
toes_ring_ref_list = [j for i, j in toes_ring_ref_dict.items()]
toes_ring_control_dict = {i: j.replace('index','ring') for i, j in toes_index_control_dict.items()}
toes_ring_control_list = [j for i, j in toes_ring_control_dict.items()]

toes_pinky_ref_dict = {'toes_pinky1':'toes_pinky1_ref', 'toes_pinky2':'toes_pinky2_ref', 'toes_pinky3':'toes_pinky3_ref'}
toes_pinky_ref_list =  [j for i, j in toes_pinky_ref_dict.items()]
toes_pinky_control_dict = {i: j.replace('index','pinky') for i, j in toes_index_control_dict.items()}
toes_pinky_control_list = [j for i, j in toes_pinky_control_dict.items()]

toes_control = toes_thumb_control_list + toes_index_control_list + toes_middle_control_list + toes_ring_control_list + toes_pinky_control_list


leg_bones_dict = {
    'upthigh':'c_thigh_b', 
    'thigh': {'base':'thigh', 'fk':'thigh_fk', 'ik':'thigh_ik', 'ik_nostr':'thigh_ik_nostr', 'control_fk':'c_thigh_fk', 'control_ik':'c_thigh_ik', 'twist':'thigh_twist', 'stretch':'thigh_stretch', 'secondary_00':'c_thigh_bend_contact', 'secondary_01':'c_thigh_bend_01', 'secondary_02':'c_thigh_bend_02'}, 
    'calf':{'base':'leg', 'fk':'leg_fk', 'ik':'leg_ik', 'ik_nostr':'leg_ik_nostr', 'control_fk':'c_leg_fk', 'twist':'leg_twist', 'stretch':'leg_stretch', 'secondary_00':'c_knee_bend', 'secondary_01':'c_leg_bend_01', 'secondary_02':'c_leg_bend_02', 'secondary_03':'c_ankle_bend'}, 
    'foot':{'fk':'foot_fk', 'control_fk':'c_foot_fk', 'snap_fk':'foot_snap_fk', 'ik':'foot_ik', 'ik_target':'foot_ik_target', 'control_ik':'c_foot_ik', 'deform':'foot', 'pole':'foot_pole', 'fk_scale_fix':'c_foot_fk_scale_fix', 'shape_override_fk':'c_p_foot_fk', 'shape_override_ik':'c_p_foot_ik', 'bank_01':'c_foot_bank_01', 'bank_02':'c_foot_bank_02', 'foot_heel':'c_foot_heel', 'control_reverse':'c_foot_01', 'pole_01':'foot_01_pole', 'roll':'c_foot_roll', 'control_roll':'c_foot_roll_cursor', 'secondary_00':'foot_bend'}, 
    'toes':{'01': 'toes_01', '02': 'toes_02', '01_ik': 'toes_01_ik', 'control_fk': 'c_toes_fk', 'control_ik':'c_toes_ik', 'toes_track': 'c_toes_track', 'toes_end': 'c_toes_end', 'toes_end_01':'c_toes_end_01'}, 
    'prepole':'leg_fk_pre_pole', 
    'control_pole_ik':'c_leg_pole',
    'fk_pole':'leg_fk_pole',
    'control_stretch':'c_stretch_leg',
    'control_pin':'c_stretch_leg_pin',
    'toes_pinky1':'c_toes_pinky1', 'toes_pinky2':'c_toes_pinky2', 'toes_pinky3':'c_toes_pinky3', 'toes_ring1':'c_toes_ring1', 'toes_ring2':'c_toes_ring2', 'toes_ring3':'c_toes_ring3', 'toes_middle1':'c_toes_middle1', 'toes_middle2':'c_toes_middle2', 'toes_middle3':'c_toes_middle3', 'toes_index1':'c_toes_index1', 'toes_index2':'c_toes_index2', 'toes_index3':'c_toes_index3', 'toes_thumb1':'c_toes_thumb1', 'toes_thumb2':'c_toes_thumb2'    
    }

leg_bones_list = []
for i, j in leg_bones_dict.items():
    if type(j) is dict:
        for k, l in j.items():
            leg_bones_list.append(l)            
    else:
        leg_bones_list.append(j)
        
    
leg_ref_bones_dict = {'heel_bank_01':'foot_bank_01_ref', 'heel_bank_02':'foot_bank_02_ref', 'heel':'foot_heel_ref', 'toes_end':'toes_end_ref', 'thigh':'thigh_ref', 'calf':'leg_ref', 'foot':'foot_ref', 'toes':'toes_ref', 'thigh_b':'thigh_b_ref', **toes_thumb_ref_dict, **toes_index_ref_dict, **toes_middle_ref_dict, **toes_ring_ref_dict, **toes_pinky_ref_dict}

leg_ref_bones_list = [j for i, j in leg_ref_bones_dict.items()]

leg_bones_rig_add = [
    leg_bones_dict['calf']['secondary_00'], leg_bones_dict['calf']['secondary_01'], leg_bones_dict['calf']['secondary_02'], leg_bones_dict['calf']['secondary_03'], leg_bones_dict['thigh']['secondary_00'], leg_bones_dict['thigh']['secondary_01'], leg_bones_dict['thigh']['secondary_02'], leg_bones_dict['foot']['secondary_00']]

leg_deform = [
    leg_bones_dict['foot']['deform'], leg_bones_dict['toes_pinky1'], leg_bones_dict['toes_pinky2'], leg_bones_dict['toes_pinky3'], leg_bones_dict['toes_ring1'], leg_bones_dict['toes_ring2'], leg_bones_dict['toes_ring3'], leg_bones_dict['toes_middle1'], leg_bones_dict['toes_middle2'], leg_bones_dict['toes_middle3'], leg_bones_dict['toes_index1'], leg_bones_dict['toes_index2'], leg_bones_dict['toes_index3'], leg_bones_dict['toes_thumb1'], leg_bones_dict['toes_thumb2'], leg_bones_dict['toes']['01'], leg_bones_dict['thigh']['twist'], leg_bones_dict['calf']['stretch'], leg_bones_dict['calf']['twist'], leg_bones_dict['thigh']['stretch'], leg_bones_dict['upthigh']]

leg_control = [
    leg_bones_dict['upthigh'], leg_bones_dict['thigh']['control_fk'], leg_bones_dict['thigh']['control_ik'], leg_bones_dict['calf']['control_fk'], leg_bones_dict['toes_pinky1'], leg_bones_dict['toes_pinky2'], leg_bones_dict['toes_pinky3'], leg_bones_dict['toes_ring1'], leg_bones_dict['toes_ring2'], leg_bones_dict['toes_ring3'], leg_bones_dict['toes_middle1'], leg_bones_dict['toes_middle2'], leg_bones_dict['toes_middle3'], leg_bones_dict['toes_index1'], leg_bones_dict['toes_index2'], leg_bones_dict['toes_index3'], leg_bones_dict['toes_thumb1'], leg_bones_dict['toes_thumb2'], leg_bones_dict['foot']['control_fk'], leg_bones_dict['toes']['control_fk'], leg_bones_dict['control_stretch'], leg_bones_dict['calf']['secondary_03'], leg_bones_dict['calf']['secondary_02'], leg_bones_dict['calf']['secondary_01'], leg_bones_dict['calf']['secondary_00'], leg_bones_dict['thigh']['secondary_02'], leg_bones_dict['thigh']['secondary_01'], leg_bones_dict['thigh']['secondary_00'], leg_bones_dict['control_pin'], leg_bones_dict['foot']['control_ik'], leg_bones_dict['toes']['control_ik'], leg_bones_dict['foot']['control_reverse'], leg_bones_dict['foot']['control_roll'], leg_bones_dict['control_pole_ik']]

leg_props = {'soft_ik': 'leg_softik'}


# HEAD
skulls_dict = {
    '01':'c_skull_01.x',
    '02':'c_skull_02.x',
    '03':'c_skull_03.x'
    }
    
skulls = [j for i, j in skulls_dict.items()]
heads_dict = {
    'deform':'head.x',
    'control':'c_head.x',
    'scale_fix':'head_scale_fix.x',
    'shape_override':'c_p_head.x'
    }
head_deform = [heads_dict['deform']] + skulls
head_control = [heads_dict['control']] + skulls
head_bones = [j for i, j in heads_dict.items()] + skulls
head_ref = ['head_ref.x']

#   facial
facial_ref = ['eyebrow_full_ref', 'eyebrow_03_ref', 'eyebrow_02_ref', 'eyebrow_01_ref', 'eyebrow_01_end_ref', 'lips_top_ref.x', 'lips_top_ref', 'lips_top_01_ref', 'lips_smile_ref', 'lips_corner_mini_ref', 'lips_bot_ref.x', 'lips_bot_ref', 'lips_bot_01_ref', 'lips_roll_top_ref.x', 'lips_roll_bot_ref.x', 'tong_01_ref.x', 'tong_02_ref.x', 'tong_03_ref.x', 'teeth_bot_ref.x', 'teeth_bot_ref', 'chin_02_ref.x', 'chin_01_ref.x', 'teeth_top_ref.x', 'teeth_top_ref', 'eye_offset_ref', 'eyelid_top_ref', 'eyelid_bot_ref', 'eyelid_top_01_ref', 'eyelid_top_02_ref', 'eyelid_top_03_ref', 'eyelid_bot_01_ref', 'eyelid_bot_02_ref', 'eyelid_bot_03_ref', 'eyelid_corner_01_ref', 'eyelid_corner_02_ref', 'cheek_smile_ref', 'cheek_inflate_ref', 'nose_01_ref.x', 'nose_02_ref.x', 'nose_03_ref.x', 'jaw_ref.x']  

facial_deform =['c_teeth_bot.x', 'c_teeth_top', 'c_teeth_bot', 'c_teeth_top.x', 'jawbone.x', 'c_lips_bot', 'c_lips_bot_01', 'c_lips_bot.x', 'c_lips_smile', 'c_lips_top.x', 'c_lips_top', 'c_lips_top_01',  'c_eye', 'c_chin_01.x', 'c_chin_02.x', 'c_eye_offset', 'c_cheek_smile', 'c_nose_03.x', 'c_nose_01.x', 'c_nose_02.x', 'c_cheek_inflate', 'c_eye_ref_track', 'tong_03.x', 'tong_02.x', 'tong_01.x', 'c_eyebrow_03', 'c_eyebrow_02', 'c_eyebrow_01', 'c_eyebrow_01_end', 'c_eyelid_top_01', 'c_eyelid_top_02', 'c_eyelid_top_03', 'c_eyelid_bot_01', 'c_eyelid_bot_02', 'c_eyelid_bot_03', 'c_eyelid_corner_01', 'c_eyelid_corner_02']

facial_control = ['c_teeth_top_master.x', 'c_teeth_bot_master.x', 'c_teeth_bot.x', 'c_teeth_top', 'c_teeth_bot', 'c_teeth_top.x', 'c_tong_03.x', 'c_tong_02.x', 'c_tong_01.x', 'c_cheek_inflate', 'c_nose_03.x', 'c_nose_01.x', 'c_nose_02.x', 'c_eye_offset', 'c_cheek_smile', 'c_chin_01.x', 'c_chin_02.x', 'c_eye', 'c_lips_smile', 'c_lips_top', 'c_lips_top_01', 'c_lips_top.x', 'c_lips_bot', 'c_lips_bot_01', 'c_lips_bot.x', 'c_jawbone.x', 'c_tong_01.x', 'c_tong_02.x', 'c_tong_03.x', 'c_lips_corner_mini', 'c_lips_roll_top.x', 'c_lips_roll_bot.x', 'c_eyelid_top', 'c_eyelid_bot', 'c_eyebrow_full', 'c_eyebrow_03', 'c_eyebrow_02', 'c_eyebrow_01', 'c_eyebrow_01_end', 'c_eye_target.x', 'c_eye_target', 'c_eye_ref', 'c_eyelid_top_01', 'c_eyelid_top_02', 'c_eyelid_top_03', 'c_eyelid_bot_01', 'c_eyelid_bot_02', 'c_eyelid_bot_03', 'c_eyelid_corner_01', 'c_eyelid_corner_02']

facial_bones = ['c_eye_ref_track', 'c_jawbone.x', 'jawbone.x', 'c_tong_01.x', 'c_tong_02.x', 'c_tong_03.x', 'tong_03.x', 'tong_02.x', 'tong_01.x', 'c_chin_01.x', 'c_chin_02.x', 'c_teeth_bot_master.x', 'c_teeth_bot.x', 'c_teeth_bot', 'c_lips_bot_01_offset', 'c_lips_bot_01', 'c_lips_bot_offset', 'c_lips_bot', 'c_lips_bot_offset.x', 'c_lips_bot.x', 'c_lips_roll_bot.x', 'c_lips_roll_top.x', 'c_teeth_top_master.x', 'c_teeth_top.x', 'c_teeth_top', 'jaw_ret_bone.x', 'c_lips_top_retain.x', 'c_lips_top_retain', 'c_lips_top_01_retain', 'c_lips_smile_retain', 'c_lips_bot_01_retain', 'c_lips_bot_retain', 'c_lips_bot_retain.x', 'c_lips_top_offset.x', 'c_lips_top.x', 'c_lips_top_offset', 'c_lips_top', 'c_lips_top_01_offset', 'c_lips_top_01', 'c_lips_smile_offset', 'c_lips_smile', 'c_lips_corner_mini', 'c_eye_offset', 'c_eyelid_base', 'c_eyelid_top', 'c_eyelid_top_01', 'c_eyelid_top_02', 'c_eyelid_top_03', 'c_eyelid_bot', 'c_eyelid_bot_01', 'c_eyelid_bot_02', 'c_eyelid_bot_03', 'c_eye', 'c_eye_ref', 'c_eyelid_corner_01', 'c_eyelid_corner_02', 'eyelid_top', 'eyelid_bot', 'c_cheek_smile', 'c_nose_03.x', 'c_nose_01.x', 'c_nose_02.x', 'c_cheek_inflate', 'c_eyebrow_full', 'c_eyebrow_03', 'c_eyebrow_02', 'c_eyebrow_01', 'c_eyebrow_01_end', 'c_eye_target.x', 'c_eye_target', 'lips_top_follow', 'lips_top_01_follow', 'lips_bot_follow', 'lips_bot_01_follow']


# EARS
ear_ref = ['ear_01_ref', 'ear_02_ref']
ear_control = ['c_ear_01', 'c_ear_02']

def get_ears_controllers(side):
    ears_list = []
    for ear_id in range(0,17):
        ear_n = 'ear_' + '%02d' % ear_id + '_ref' + side
        if bpy.context.active_object.data.bones.get(ear_n):
            ears_list.append('c_ear_' + '%02d' % ear_id + side)
    return ears_list



# NECK
neck_deform = ['c_neck_01.x', 'neck.x']
neck_control = ['c_neck.x', 'c_neck_01.x']
neck_bones = ['c_neck.x', 'c_neck_01.x', 'neck.x', 'c_p_neck.x', 'c_p_neck_01.x', 'neck_twist.x']
neck_ref = ['neck_ref.x']


# SPINE
def get_spine_name(type, idx):
    str_idx = '%02d' % idx    
    
    if type == 'ref':
        return'spine_'+str_idx+'_ref'+'.x'  
        
    elif type == 'control':
        return 'c_spine_'+str_idx+'.x'  
        
    elif type == 'control_bend':
        return 'c_spine_'+str_idx+'_bend'+'.x'   
        
    elif type == 'base':
        return 'spine_'+str_idx+'.x'        
        
    elif type == 'shape_override':
        return 'c_p_spine_'+str_idx+'.x'
        
    elif type == 'control_proxy':
        return 'c_spine_'+str_idx+'_proxy'+'.x'
        
    elif type == 'control_bend_proxy':
        return 'c_spine_'+str_idx+'_bend_proxy'+'.x'
        
        
def get_spine_idx(name):
    for i in name.split('_'):
        if i.isdigit() and len(i) == 2:
            return int(i)
            
    return None
        

spine_bones_dict = {
    'c_root_master': 'c_root_master.x', 'c_root':'c_root.x', 'root':'root.x', 'c_root_bend':'c_root_bend.x', 
    'c_waist_bend':'c_waist_bend.x', 'root_master_shape_override':'c_p_root_master.x', 'root_shape_override':'c_p_root.x', 
    'spine_01_shape_override':get_spine_name('shape_override', 1), 'spine_02_shape_override':get_spine_name('shape_override', 2), 
    'c_spine_01':get_spine_name('control', 1), 'spine_01':get_spine_name('base', 1), 'c_spine_01_bend':get_spine_name('control_bend', 1), 
    'c_spine_02':get_spine_name('control', 2), 'spine_02':get_spine_name('base', 2), 'c_spine_02_bend':get_spine_name('control_bend', 2)}

spine_bones = [j for i, j in spine_bones_dict.items()]

spine03_deform = [get_spine_name('base', 3)]
spine03_control = [get_spine_name('control', 3), get_spine_name('control_proxy', 3), get_spine_name('control_bend', 3)]

spine02_deform = [spine_bones_dict['c_spine_02_bend'], spine_bones_dict['spine_02']]
spine02_control = [spine_bones_dict['c_spine_02'], spine_bones_dict['c_spine_02_bend'], get_spine_name('control_proxy', 2), get_spine_name('control_bend_proxy', 2)]

spine01_deform = [spine_bones_dict['c_spine_01_bend'], spine_bones_dict['spine_01']]

spine01_control = [spine_bones_dict['c_spine_01'], spine_bones_dict['c_spine_01_bend'], get_spine_name('control_proxy', 1), get_spine_name('control_bend_proxy', 1)]

spine_ref_dict = {'root':'root_ref.x', 'spine_01':get_spine_name('ref', 1), 'spine_02': get_spine_name('ref', 2)}

spine_ref_list = [j for i, j in spine_ref_dict.items()]

spine_bones_rig_add = [spine_bones_dict['c_waist_bend'], 'c_waist_bend_end.x', 'epaules_bend.x']

spine_control = spine01_control + spine02_control + [spine_bones_dict['c_root'], spine_bones_dict['c_root_master'], spine_bones_dict['c_root_bend']]


# SPLINE IK
spline_ik_bones = ['c_spline_root', 'spline_stretch', 'c_spline_curvy', 'c_spline_tip']


# Tail
tail_bones = ['c_tail_master']


#SMART FACIAL MARKERS
facial_markers = {'eyebrow_01_end.l': 15, 'eyebrow_01.l':16, 'eyebrow_02.l':17, 'eyebrow_03.l':18, 'eyebrow_01_end.r':40, 'eyebrow_01.r':41, 'eyebrow_02.r':42, 'eyebrow_03.r':43,'eyelid_corner_01.l':7, 'eyelid_bot_01.l':6, 'eyelid_bot_02.l':5, 'eyelid_bot_03.l':12, 'eyelid_corner_02.l':11, 'eyelid_top_03.l':10, 'eyelid_top_02.l':9, 'eyelid_top_01.l':8, 'eyelid_corner_01.r':30, 'eyelid_bot_01.r':29, 'eyelid_bot_02.r':28, 'eyelid_bot_03.r':35, 'eyelid_corner_02.r':34, 'eyelid_top_03.r':33, 'eyelid_top_02.r':32, 'eyelid_top_01.r':31,'nose_03.x':36, 'nose_01.x':37, 'cheek_smile.l':13, 'cheek_inflate.l':14, 'cheek_smile.r':38, 'cheek_inflate.r':39, 'lips_top.x':22, 'lips_top.l':0, 'lips_top_01.l':1, 'lips_smile.l':2, 'lips_bot_01.l':3, 'lips_bot.l':4, 'lips_bot.x':21, 'lips_top.r':23, 'lips_top_01.r':24, 'lips_smile.r':25, 'lips_bot_01.r':26, 'lips_bot.r':27,'chin_01.x': 47, 'chin_02.x':46, 'ear_01.l':20, 'ear_02.l':19, 'ear_01.r':45, 'ear_02.r':44}



#UPDATE
bones_arp_layer = {'c_eyebrow_01_proxy.l': 0, 'c_index2.l': 0, 'c_index1_base.r': 0, 'c_eyelid_bot_01_proxy.l': 1, 'c_neck_thick_proxy.x': 1, 'c_pinky1.l': 0, 'c_eyebrow_03_proxy.l': 0, 'c_foot_01_proxy.l': 0, 'c_eyelid_bot_03.l': 1, 'c_spine_01_proxy.x': 0, 'c_breast_01_proxy.r': 1, 'c_thumb1.l': 0, 'c_eyebrow_03.l': 0, 'c_eyelid_top_03_proxy.r': 1, 'c_pinky2.l': 0, 'c_eyelid_corner_02_proxy.l': 1, 'c_toes_ring2_proxy.l': 0, 'c_leg_bend_02_proxy.r': 1, 'c_toes_fk.l': 0, 'c_cheek_inflate.r': 1, 'c_toes_index3_proxy.r': 0, 'c_hand_ik_proxy.r': 0, 'c_thigh_bend_contact.r': 1, 'c_thigh_bend_contact.l': 1, 'c_eye_ref.l': 1, 'c_eyelid_top_03.l': 1, 'c_eyebrow_01_end_proxy.r': 0, 'c_lips_roll_bot_proxy.x': 0, 'c_toes_ring3_proxy.r': 0, 'c_eyebrow_full_proxy.l': 0, 'c_chin_02.x': 1, 'c_nose_02.x': 1, 'c_foot_01.l': 0, 'c_toes_ring3.r': 0, 'c_ring3.l': 0, 'c_ring2_proxy.r': 0, 'c_skull_01_proxy.x': 1, 'c_toes_pinky3_proxy.r': 0, 'c_toes_thumb1_proxy.l': 0, 'c_cheek_smile_proxy.l': 1, 'c_pinky1_base_proxy.r': 0, 'c_index1.l': 0, 'c_thigh_bend_02_proxy.r': 1, 'c_chin_02_proxy.x': 1, 'c_toes_pinky2_proxy.r': 0, 'c_foot_01_proxy.r': 0, 'c_lips_bot_01_proxy.r': 0, 'c_waist_bend.x': 1, 'c_eyebrow_02.l': 0, 'c_cheek_smile.l': 1, 'c_toes_middle3_proxy.l': 0, 'c_eyelid_bot_02_proxy.l': 1, 'c_breast_01_proxy.l': 1, 'c_toes_pinky3.l': 0, 'c_toes_middle3_proxy.r': 0, 'c_toes_index2.r': 0, 'c_index3_proxy.r': 0, 'c_skull_03_proxy.x': 1, 'c_neck.x': 0, 'c_head_proxy.x': 0, 'c_index1_proxy.r': 0, 'c_ring3_proxy.r': 0, 'c_tong_02_proxy.x': 0, 'c_toes_pinky1_proxy.l': 0, 'c_ring1_base_proxy.r': 0, 'c_index1_base_proxy.r': 0, 'c_eyebrow_full.l': 0, 'c_toes_thumb2_proxy.r': 0, 'c_root.x': 0, 'c_eyelid_corner_01.r': 1, 'c_cheek_smile.r': 1, 'c_eyelid_bot_01.l': 1, 'c_middle3_proxy.r': 0, 'c_teeth_top_proxy.x': 0, 'c_toes_index1_proxy.r': 0, 'c_skull_02_proxy.x': 1, 'c_thumb1_base.r': 0, 'c_thigh_bend_02_proxy.l': 1, 'c_lips_top_01_proxy.l': 0, 'c_lips_bot.x': 0, 'c_eyelid_bot_02.r': 1, 'c_arm_twist_offset.l': 0, 'c_lips_smile.l': 0, 'c_stretch_leg_proxy.r': 1, 'c_toes_ring3.l': 0, 'c_morph_jaw_round': 16, 'c_eye_offset.l': 1, 'c_lips_smile_proxy.l': 0, 'c_tong_01.x': 0, 'c_eye_ref.r': 1, 'c_thigh_bend_contact_proxy.r': 1, 'c_toes_ring2.r': 0, 'c_leg_bend_01.r': 1, 'c_thigh_fk_proxy.r': 0, 'c_eyebrow_01_end.r': 0, 'c_hand_ik_proxy.l': 0, 'c_traj_proxy': 0, 'c_pinky2.r': 0, 'c_elbow_bend.l': 1, 'c_lips_bot_proxy.l': 0, 'c_shoulder_bend.l': 1, 'c_shoulder_proxy.r': 0, 'c_foot_ik.l': 0, 'c_eyelid_bot_01.r': 1, 'c_leg_pole_proxy.l': 0, 'c_skull_02.x': 1, 'c_ankle_bend.r': 1, 'c_eyelid_corner_01_proxy.l': 1, 'c_middle3.r': 0, 'c_foot_fk.r': 0, 'c_eyelid_bot_proxy.r': 0, 'c_morph_mouth': 16, 'c_leg_bend_02.r': 1, 'c_eyelid_top.l': 0, 'c_thigh_bend_02.r': 1, 'c_hand_fk.r': 0, 'c_hand_fk_proxy.r': 0, 'c_pos_proxy': 0, 'c_leg_bend_01_proxy.l': 1, 'c_eye_offset_proxy.r': 1, 'c_arms_pole_proxy.l': 0, 'c_thigh_fk.r': 0, 'c_eyelid_top_03.r': 1, 'c_stretch_leg_pin_proxy.l': 1, 'c_lips_roll_bot.x': 0, 'c_ring1.r': 0, 'c_ring1.l': 0, 'c_thumb2.r': 0, 'c_forearm_bend_proxy.l': 1, 'c_lips_top_proxy.x': 0, 'c_index2_proxy.r': 0, 'c_toes_pinky3_proxy.l': 0, 'c_thigh_bend_01_proxy.r': 1, 'c_root_master.x': 0, 'c_nose_01_proxy.x': 1, 'c_skull_03.x': 1, 'c_thumb2_proxy.r': 0, 'c_arm_fk.l': 0, 'c_toes_thumb2.r': 0, 'c_jawbone_proxy.x': 0, 'c_spine_01_bend.x': 1, 'c_eyelid_top_proxy.r': 0, 'c_index3.r': 0, 'c_middle3_proxy.l': 0, 'c_arm_fk_proxy.r': 0, 'c_eyelid_bot_02_proxy.r': 1, 'c_tail_03_proxy.x': 0, 'c_middle1_proxy.l': 0, 'c_foot_fk_proxy.r': 0, 'c_lips_bot_01_proxy.l': 0, 'c_eye_target.r': 0, 'c_toes_thumb2.l': 0, 'c_toes_index3_proxy.l': 0, 'c_thumb1_base_proxy.l': 0, 'c_thigh_b_proxy.l': 1, 'c_leg_fk.l': 0, 'c_thigh_bend_01.r': 1, 'c_jawbone.x': 0, 'c_thigh_b.r': 1, 'c_toes_thumb1.r': 0, 'c_skull_01.x': 1, 'c_toes_index3.r': 0, 'c_toes_middle2_proxy.r': 0, 'c_middle1.l': 0, 'c_toes_fk_proxy.r': 0, 'c_lips_top.x': 0, 'c_shoulder.l': 0, 'c_index2_proxy.l': 0, 'c_toes_thumb1_proxy.r': 0, 'c_index3_proxy.l': 0, 'c_eye_proxy.r': 0, 'c_eye_offset.r': 1, 'c_middle1_base.l': 0, 'c_stretch_arm.r': 1, 'c_index1_base_proxy.l': 0, 'c_toes_index3.l': 0, 'c_nose_01.x': 1, 'c_eye_target_proxy.x': 0, 'c_neck_01.x': 1, 'c_middle2_proxy.r': 0, 'c_eyelid_top_02.r': 1, 'c_toes_index2_proxy.l': 0, 'c_arms_pole.r': 0, 'c_toes_ik.r': 0, 'c_pinky2_proxy.l': 0, 'c_lips_smile_proxy.r': 0, 'c_pinky3_proxy.r': 0, 'c_morph_eyelashes_size': 16, 'c_pinky2_proxy.r': 0, 'c_tail_02_proxy.x': 0, 'c_ring3.r': 0, 'c_eyebrow_02_proxy.l': 0, 'c_toes_fk.r': 0, 'c_thumb1.r': 0, 'c_toes_index1_proxy.l': 0, 'c_eyelid_bot_02.l': 1, 'c_wrist_bend.r': 1, 'c_foot_roll_cursor.r': 0, 'c_arm_bend_proxy.r': 1, 'c_toes_ring2.l': 0, 'c_pinky1_proxy.l': 0, 'c_toes_ring1.l': 0, 'c_toes_middle2.l': 0, 'c_stretch_leg_pin.r': 1, 'c_toes_middle1.l': 0, 'c_pinky3.r': 0, 'c_toes_index1.l': 0, 'c_eye_target_proxy.l': 0, 'c_lips_top_proxy.r': 0, 'c_knee_bend_proxy.r': 1, 'c_spine_01.x': 0, 'c_breast_02_proxy.r': 1, 'c_leg_pole.l': 0, 'c_nose_03_proxy.x': 1, 'c_lips_smile.r': 0, 'c_eye.l': 0, 'c_bot_bend.l': 1, 'c_stretch_arm_pin_proxy.l': 1, 'c_tong_03.x': 0, 'c_toes_middle3.l': 0, 'c_eyelid_bot.l': 0, 'c_toes_ik.l': 0, 'c_knee_bend.l': 1, 'c_ankle_bend_proxy.r': 1, 'c_eye_ref_proxy.r': 0, 'c_index1_proxy.l': 0, 'c_shoulder.r': 0, 'c_leg_fk.r': 0, 'c_pinky1.r': 0, 'c_toes_thumb2_proxy.l': 0, 'c_cheek_smile_proxy.r': 1, 'c_tong_02.x': 0, 'c_lips_top.r': 0, 'c_shoulder_bend.r': 1, 'c_lips_bot.r': 0, 'c_spine_02_bend_proxy.x': 1, 'c_wrist_bend.l': 1, 'c_spine_02.x': 0, 'c_ring1_proxy.l': 0, 'c_thumb1_base.l': 0, 'c_leg_pole_proxy.r': 0, 'c_lips_bot_01.l': 0, 'c_thigh_bend_01.l': 1, 'c_eyelid_top_01_proxy.r': 1, 'c_thumb3_proxy.r': 0, 'c_forearm_fk_proxy.r': 0, 'c_thigh_fk_proxy.l': 0, 'c_lips_bot_proxy.x': 0, 'c_thumb3.l': 0, 'c_eyelid_top.r': 0, 'c_eyelid_bot_01_proxy.r': 1, 'c_cheek_inflate.l': 1, 'c_elbow_bend_proxy.l': 1, 'c_stretch_leg_pin_proxy.r': 1, 'c_toes_middle1_proxy.r': 0, 'c_thigh_bend_02.l': 1, 'c_foot_roll_cursor_proxy.r': 0, 'c_hand_fk.l': 0, 'c_lips_top_01.l': 0, 'c_forearm_bend.r': 1, 'c_foot_ik_proxy.r': 0, 'c_thumb2_proxy.l': 0, 'c_eyebrow_01_end_proxy.l': 0, 'c_toes_middle2_proxy.l': 0, 'c_cheek_inflate_proxy.l': 1, 'c_nose_03.x': 1, 'c_tail_01_proxy.x': 0, 'c_eyelid_top_03_proxy.l': 1, 'c_stretch_arm_pin.r': 1, 'c_middle1.r': 0, 'c_arm_fk.r': 0, 'c_eyelid_corner_01.l': 1, 'c_teeth_bot.x': 0, 'c_toes_thumb1.l': 0, 'c_ring1_proxy.r': 0, 'c_leg_bend_01.l': 1, 'c_eyebrow_02.r': 0, 'c_arms_pole.l': 0, 'c_toes_index2.l': 0, 'c_pinky1_base.l': 0, 'c_root_proxy.x': 0, 'c_toes_ik_proxy.l': 0, 'c_eye_ref_proxy.l': 0, 'c_ring1_base.l': 0, 'c_ring1_base.r': 0, 'c_leg_bend_02.l': 1, 'c_eyelid_corner_02.l': 1, 'c_eyelid_bot_03_proxy.r': 1, 'c_toes_ik_proxy.r': 0, 'c_thigh_b_proxy.r': 1, 'c_arm_bend_proxy.l': 1, 'c_eyebrow_03_proxy.r': 0, 'c_toes_index2_proxy.r': 0, 'c_arm_twist_offset_proxy.r': 0, 'c_thigh_bend_contact_proxy.l': 1, 'c_toes_middle3.r': 0, 'c_toes_ring1.r': 0, 'c_shoulder_proxy.l': 0, 'c_foot_roll_cursor_proxy.l': 0, 'c_leg_pole.r': 0, 'c_eyebrow_01_end.l': 0, 'c_eyelid_corner_02.r': 1, 'c_stretch_leg.r': 1, 'c_lips_corner_mini.r': 0, 'c_lips_roll_top.x': 0, 'c_eyelid_top_02_proxy.l': 1, 'c_cheek_inflate_proxy.r': 1, 'c_breast_02_proxy.l': 1, 'c_teeth_top.x': 0, 'c_leg_fk_proxy.l': 0, 'c_eyelid_top_proxy.l': 0, 'c_forearm_fk.r': 0, 'c_teeth_bot_proxy.x': 0, 'c_toes_ring1_proxy.r': 0, 'c_iris.r': 16, 'c_toes_pinky2.r': 0, 'c_middle1_base.r': 0, 'c_eye_target_proxy.r': 0, 'c_index1.r': 0, 'c_eyelid_bot_03.r': 1, 'c_tong_01_proxy.x': 0, 'c_pinky1_base_proxy.l': 0, 'c_middle1_proxy.r': 0, 'c_chin_01.x': 1, 'c_index2.r': 0, 'c_arms_pole_proxy.r': 0, 'c_root_master_proxy.x': 0, 'c_eyelid_top_01.r': 1, 'c_eyebrow_01_proxy.r': 0, 'c_middle1_base_proxy.r': 0, 'c_bot_bend_proxy.l': 1, 'c_pinky3_proxy.l': 0, 'layer_disp_second': 16, 'c_bot_bend.r': 1, 'c_index3.l': 0, 'c_toes_middle2.r': 0, 'c_elbow_bend.r': 1, 'c_lips_corner_mini_proxy.l': 0, 'c_lips_top_01_proxy.r': 0, 'c_thumb2.l': 0, 'c_toes_fk_proxy.l': 0, 'c_waist_bend_proxy.x': 1, 'c_middle1_base_proxy.l': 0, 'c_pinky3.l': 0, 'c_pupil.r': 16, 'c_eyelid_bot_03_proxy.l': 1, 'layer_disp_hair_long.001': 16, 'c_eyebrow_full_proxy.r': 0, 'c_eyelid_top_02_proxy.r': 1, 'c_eyebrow_01.r': 0, 'c_toes_index1.r': 0, 'c_middle2.l': 0, 'c_thigh_fk.l': 0, 'c_forearm_bend.l': 1, 'c_eyelid_top_02.l': 1, 'c_neck_proxy.x': 0, 'c_ring2.r': 0, 'c_ring3_proxy.l': 0, 'c_eyebrow_03.r': 0, 'c_lips_corner_mini_proxy.r': 0, 'c_nose_02_proxy.x': 1, 'c_foot_01.r': 0, 'c_thumb3.r': 0, 'c_toes_pinky2_proxy.l': 0, 'c_toes_ring2_proxy.r': 0, 'c_eyelid_bot_proxy.l': 0, 'c_knee_bend.r': 1, 'c_toes_pinky1.r': 0, 'c_shoulder_bend_proxy.r': 1, 'c_middle2.r': 0, 'c_toes_pinky1.l': 0, 'c_chin_01_proxy.x': 1, 'c_ring2_proxy.l': 0, 'c_spine_02_bend.x': 1, 'c_traj': 0, 'c_thumb3_proxy.l': 0, 'c_thumb1_proxy.l': 0, 'c_eyelid_top_01_proxy.l': 1, 'c_arm_fk_proxy.l': 0, 'c_arm_bend.r': 1, 'c_eye_target.l': 0, 'c_forearm_fk_proxy.l': 0, 'c_arm_twist_offset_proxy.l': 0, 'c_toes_ring1_proxy.l': 0, 'c_hand_fk_proxy.l': 0, 'c_pinky1_base.r': 0, 'c_eyelid_bot.r': 0, 'c_forearm_fk.l': 0, 'c_pupil.l': 16, 'c_toes_pinky2.l': 0, 'c_forearm_bend_proxy.r': 1, 'c_pinky1_proxy.r': 0, 'c_ring2.l': 0, 'c_stretch_arm_proxy.r': 1, 'c_eye_target.x': 0, 'c_root_bend.x': 1, 'c_morph_lip_up_size': 16, 'c_wrist_bend_proxy.l': 1, 'c_ring1_base_proxy.l': 0, 'c_head.x': 0, 'c_stretch_leg_proxy.l': 1, 'c_elbow_bend_proxy.r': 1, 'c_foot_fk.l': 0, 'c_arm_twist_offset.r': 0, 'c_toes_pinky1_proxy.r': 0, 'c_lips_roll_top_proxy.x': 0, 'c_lips_top_01.r': 0, 'layer_disp_main': 16, 'c_thigh_bend_01_proxy.l': 1, 'c_iris.l': 16, 'c_eyelid_corner_01_proxy.r': 1, 'c_lips_bot.l': 0, 'c_lips_bot_01.r': 0, 'c_root_bend_proxy.x': 1, 'c_eyebrow_full.r': 0, 'c_toes_middle1_proxy.l': 0, 'c_middle3.l': 0, 'c_arm_bend.l': 1, 'c_thigh_b.l': 1, 'c_hand_ik.l': 0, 'c_stretch_arm.l': 1, 'c_foot_ik_proxy.l': 0, 'c_spine_01_bend_proxy.x': 1, 'c_foot_fk_proxy.l': 0, 'c_lips_top_proxy.l': 0, 'c_toes_ring3_proxy.l': 0, 'c_lips_top.l': 0, 'c_stretch_arm_proxy.l': 1, 'c_eyelid_corner_02_proxy.r': 1, 'c_index1_base.l': 0, 'c_ankle_bend.l': 1, 'c_eye.r': 0, 'c_bot_bend_proxy.r': 1, 'c_foot_roll_cursor.l': 0, 'c_hand_ik.r': 0, 'c_eyebrow_02_proxy.r': 0, 'c_toes_middle1.r': 0, 'c_middle2_proxy.l': 0, 'c_stretch_arm_pin_proxy.r': 1, 'c_leg_bend_01_proxy.r': 1, 'c_eyebrow_01.l': 0, 'c_eyelid_top_01.l': 1, 'c_eye_proxy.l': 0, 'c_ankle_bend_proxy.l': 1, 'c_morph_lip_bot_size': 16, 'c_leg_fk_proxy.r': 0, 'c_stretch_leg_pin.l': 1, 'c_eye_offset_proxy.l': 1, 'c_lips_corner_mini.l': 0, 'c_shoulder_bend_proxy.l': 1, 'c_pos': 0, 'c_foot_ik.r': 0, 'c_knee_bend_proxy.l': 1, 'c_lips_bot_proxy.r': 0, 'c_tail_00_proxy.x': 0, 'c_spine_02_proxy.x': 0, 'c_toes_pinky3.r': 0, 'c_tong_03_proxy.x': 0, 'c_thumb1_base_proxy.r': 0, 'c_stretch_arm_pin.l': 1, 'c_leg_bend_02_proxy.l': 1, 'c_stretch_leg.l': 1, 'c_thumb1_proxy.r': 0, 'c_wrist_bend_proxy.r': 1}  

bone_update_locations = {'c_breast_01_proxy.l': (Vector((0.04883772134780884, -0.5081361532211304, -2.3916122913360596)), Vector((0.04883772134780884, -0.5081361532211304, -2.3670592308044434))), 'c_spine_01_proxy.x': (Vector((-2.3961765691637993e-06, -0.5081361532211304, -2.4267547130584717)), Vector((-2.3961765691637993e-06, -0.5081361532211304, -2.4161593914031982))), 'c_spine_02_bend_proxy.x': (Vector((-0.00014736957382410765, -0.5081361532211304, -2.3936164379119873)), Vector((0.0038200942799448967, -0.5081361532211304, -2.3936164379119873))), 'c_breast_02_proxy.l': (Vector((0.04825196415185928, -0.5218240022659302, -2.3574445247650146)), Vector((0.04825196415185928, -0.49444830417633057, -2.3574445247650146))), 'c_spine_02_proxy.x': (Vector((0.0, -0.508139967918396, -2.3380000591278076)), Vector((0.0, -0.508139967918396, -2.327312469482422))), 'c_breast_01_proxy.r': (Vector((-0.04883772134780884, -0.5081361532211304, -2.3916122913360596)), Vector((-0.04883772134780884, -0.5081361532211304, -2.3670592308044434))), 'c_root_master_proxy.x': (Vector((-2.3961765691637993e-06, -0.5081361532211304, -2.530362367630005)), Vector((-2.3961765691637993e-06, -0.5081361532211304, -2.5166168212890625))), 'c_root_proxy.x': (Vector((-2.3961765691637993e-06, -0.5074262022972107, -2.5002286434173584)), Vector((-2.3961765691637993e-06, -0.5074262022972107, -2.489633321762085))), 'c_spine_01_bend_proxy.x': (Vector((-0.00014736957382410765, -0.5081361532211304, -2.4434287548065186)), Vector((0.0038200942799448967, -0.5081361532211304, -2.4434287548065186))), 'c_root_bend_proxy.x': (Vector((-0.00014736957382410765, -0.5081361532211304, -2.481240749359131)), Vector((0.0038200942799448967, -0.5081361532211304, -2.481240749359131))), 'c_breast_02_proxy.r': (Vector((-0.04825196415185928, -0.5218240022659302, -2.3574445247650146)), Vector((-0.04825196415185928, -0.49444830417633057, -2.3574445247650146))), 'c_waist_bend_proxy.x': (Vector((0.03724130615592003, -0.5081361532211304, -2.4630987644195557)), Vector((0.041208770126104355, -0.5081361532211304, -2.4630987644195557)))}  