#######################################################
## Reset functions for internal usage (Match to Rig)
## resets all controllers transforms (pose mode)
#######################################################

import bpy

def reset_all():
    rig = bpy.context.active_object
    
    def set_inverse_child(cns):         
        # direct inverse matrix method
        if cns.subtarget != "":
            if rig.data.bones.get(cns.subtarget):
                cns.inverse_matrix = rig.pose.bones[cns.subtarget].matrix.inverted()  
        else:
            print("Child Of constraint could not be reset, bone does not exist:", cns.subtarget, cns.name)      
        
    # Reset transforms------------------------------
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.rot_clear()
    # "scale clear" leads to resetting bbones_easeout/in value, we need to preserve them
    bdict = {}
    for b in rig.pose.bones:
        bdict[b.name] = [b.bbone_easein, b.bbone_easeout]
        
    bpy.ops.pose.scale_clear()
    
    for bname in bdict:
        pbone = rig.pose.bones[bname]
        pbone.bbone_easein, pbone.bbone_easeout = bdict[bname]
    
    for pbone in rig.pose.bones:       
        # Reset locked transforms       
        for i, rot in enumerate(pbone.rotation_euler):
            if pbone.lock_rotation[i]:                                
                pbone.rotation_euler[i] = 0.0
        
        # Reset Properties
        if len(pbone.keys()) > 0:
            for key in pbone.keys():
                
                if 'ik_fk_switch' in key:
                    found_RNA_UI = '_RNA_UI' in pbone.keys()
                    has_set = False
                    
                    if found_RNA_UI:
                        if 'default' in pbone['_RNA_UI']['ik_fk_switch']:
                            pbone['ik_fk_switch'] = pbone['_RNA_UI']['ik_fk_switch']['default']
                            has_set = True
                            
                    if not has_set:
                        if 'hand' in pbone.name:
                            pbone['ik_fk_switch'] = 1.0
                        else:
                            pbone['ik_fk_switch'] = 0.0
                 
                    
                if 'stretch_length' in key:
                    pbone['stretch_length'] = 1.0
                    
                # don't set auto-stretch to 1 for now, it's not compatible with Fbx export
                # if 'auto_stretch' in key:
                #    pbone['auto_stretch'] = 1.0
                
                if 'pin' in key:
                    if 'leg' in key:
                        pbone['leg_pin'] = 0.0
                    else:
                        pbone['elbow_pin'] = 0.0
                        
                if 'bend_all' in key:
                    pbone['bend_all'] = 0.0
                    
       
        reset_child_of_bones = {'c_leg_pole':'startswith', 'c_arms_pole':'startswith', 'hand':'in', 'foot':'in', 'head':'in', 'c_thumb':'startswith', 'c_index':'startswith', 'c_middle':'startswith', 'c_ring':'startswith', 'c_pinky':'startswith', 'c_eye_target':'startswith'}
        
        valid = False
        
        if not 'cc' in pbone.keys():# do not set inverse for custom bones
            for bname in reset_child_of_bones:            
                type = reset_child_of_bones[bname]
                if type == 'startswith':
                    if pbone.name.startswith(bname):
                        valid = True
                elif type == 'in':
                    if bname in pbone.name:
                        valid = True
           
        if valid:        
            for cns in pbone.constraints:
                if cns.type == 'CHILD_OF':
                    set_inverse_child(cns)
    
    bpy.ops.pose.select_all(action='DESELECT')