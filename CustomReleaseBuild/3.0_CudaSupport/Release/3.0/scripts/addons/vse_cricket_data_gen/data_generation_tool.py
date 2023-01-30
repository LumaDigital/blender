import csv
import os
import random

import bpy

BATSMAN_STYLE_ITEMS = [("RH", "Right-Handed", ""), ("LH", "Left-Handed", "")]
BOWLER_STYLE_ITEMS = [("FB", "Fast ball", ""), ("SB", "Spin ball", "")]
ACTION_TYPE_ITEMS = [
        ("0", "0 Runs", ""),
        ("1", "1 Run", ""),
        ("2", "2 Runs", ""),
        ("3", "3 Runs", ""),
        ("4", "4 Runs", ""),
        ("6", "6 Runs", ""),
        ("B", "Bowled", ""),
        ("C", "Caught", ""),
        ("S", "Stumped", "Only valid for a Spin bowler"),
        ("R", "Run Out", ""),
        ("L", "LBW", ""),
        ("W0", "Wide", "1 run is awarded to the batting team"),
        ("N0", "No Ball bowled 0", "1 run awarded for the no ball"),
        ("N1", "No Ball bowled 1", "1 run awarded for the no ball and 1 run physically run"),
        ("N2", "No Ball bowled 2", "1 run awarded for the no ball and 2 runs physically run"),
        ("N3", "No Ball bowled 3", "1 run awarded for the no ball and 3 runs physically run"),
        ("N4", "No Ball bowled 4", "1 run awarded for the no ball and a 4 was hit"),
        ("N6", "No Ball bowled 5", "1 run awarded for the no ball and a 6 was hit")]

TEAM_A_PLAYERS_STRING = "BWL WKPR MDON MDOF GULY PNT CVR MWKT SQLG FNLG TDMN"
TEAM_B_PLAYER_STRING = "BTMN1 BTMN2"

VSE_ACTION_EVENT_NAME = 'VSE_Action_Event'
VSE_ACTION_EVENT_SIZE = 50
MAX_LENGTH_OF_ACTION_SYMBOL = 2

class Generate_Data_Files(bpy.types.Operator):
    """Generates Cricket sound and action data files in .csv format"""
    bl_label = "Generate Cricket Data"
    bl_idname = "vse.generate_data"

    FRAMES_PER_SECOND = 30
    
    def execute(self, context):
    
        frame_count = bpy.context.scene.frame_end - bpy.context.scene.frame_start
        relative_frame_difference = bpy.context.scene.frame_end - frame_count # Minus this to ensure the frames range from 0-framecount

        # Game Data Generation
        gam_csv_file_name = bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0] + "-gam.csv"
        gam_csv_file_path = os.path.join(bpy.context.scene.vse_data_output_path, gam_csv_file_name)
        with open(gam_csv_file_path, 'w') as file:
            writer = csv.writer(file)

            clip_duration = int(self.get_frame_in_miliseconds(frame_count))
            frame_relative_to_frame_count = (
                context.scene.sequence_editor.sequences_all.get(VSE_ACTION_EVENT_NAME).frame_start - relative_frame_difference)
            time_of_action = int(self.get_frame_in_miliseconds(frame_relative_to_frame_count))

            gam_row = [clip_duration,
                bpy.context.scene.vse_batsman_style,
                bpy.context.scene.vse_bowler_style,
                bpy.context.scene.vse_action_type,
                time_of_action,
                TEAM_B_PLAYER_STRING + " " + TEAM_A_PLAYERS_STRING, # Spec document requires batsmen in teamA list
                TEAM_B_PLAYER_STRING]

            writer.writerow(gam_row)

        # Audio Data Generation
        aud_csv_file_name = bpy.path.basename(bpy.context.blend_data.filepath).split('.')[0] + "-aud.csv"
        aud_csv_file_path = os.path.join(bpy.context.scene.vse_data_output_path, aud_csv_file_name)
        with open(aud_csv_file_path, 'w', newline='') as file:
            writer = csv.writer(file)

            sound_list = (element for element in context.scene.sequence_editor.sequences_all if element.type == "SOUND")
            ordered_sound_list = sorted(sound_list, key=lambda x: x.frame_start)
            strips_to_exclude = []
            for x in range(len(ordered_sound_list)):

                current_strip = ordered_sound_list[x]
                current_strip_sound_name = bpy.path.basename(current_strip.sound.filepath)
                last_looped_strip_end_frame = current_strip.frame_final_end

                exclude_row = False
                for excluded_loop_strip in strips_to_exclude:
                    if current_strip == excluded_loop_strip:
                        exclude_row = True
                        break

                if exclude_row:
                    continue
                        
                loop = 'F'
                for y in range(x, len(ordered_sound_list)):

                    if (y != len(ordered_sound_list) - 1):
                        next_strip_sound_name = bpy.path.basename(ordered_sound_list[y + 1].sound.filepath)
                        next_strip_start_frame = ordered_sound_list[y + 1].frame_start

                        # No looping sound function in Blender, therefore a check for same sounds with start points right after the end point of-
                        # the previous strip will dictate whether it's looping or not (As this is the workaround)
                        if (current_strip_sound_name == next_strip_sound_name and
                            next_strip_start_frame == last_looped_strip_end_frame):
                                loop = 'T'
                                strips_to_exclude.append(ordered_sound_list[y + 1])
                                last_looped_strip_end_frame = ordered_sound_list[y + 1].frame_final_end



                aud_row = [current_strip.frame_start - relative_frame_difference,
                    current_strip_sound_name,
                    'P',
                    round(current_strip.volume, 2),
                    loop]

                writer.writerow(aud_row)

        return {"FINISHED"}

    def get_frame_in_miliseconds(self, value):
        return (value / self.FRAMES_PER_SECOND) * 1000


class Derive_Settings_from_Name(bpy.types.Operator):
    """Configures the settings below based on cutscene blend name"""
    bl_label = "Derive cutscene settings"
    bl_idname = "vse.derive_cutscene_settings"

    CUTSCENE_NAME_DILIMETER = '-'
    
    def execute(self, context):

        list_of_symbols = bpy.path.basename(bpy.context.blend_data.filepath).split(self.CUTSCENE_NAME_DILIMETER)
        for x in range(len(list_of_symbols)):

            symbol = list_of_symbols[x]
            if len(symbol) > MAX_LENGTH_OF_ACTION_SYMBOL:
                symbol = symbol[:MAX_LENGTH_OF_ACTION_SYMBOL]

            for batsman_style in BATSMAN_STYLE_ITEMS:
                if symbol in batsman_style:
                    bpy.context.scene.vse_batsman_style = symbol

            for bowler_style in BOWLER_STYLE_ITEMS:
                if symbol in bowler_style:
                    bpy.context.scene.vse_bowler_style = symbol

            for action_type in ACTION_TYPE_ITEMS:
                if symbol in action_type:
                    bpy.context.scene.vse_action_type = symbol

        return {"FINISHED"}

class Sound_System():

    RANDOM_IDENTIFIER = "Random"

    def get_default_sound(self):
        return 1

    # Bat
    def get_bat_sounds(scene, context):
        return Sound_System._create_audio_type_list("Bat")

    def add_bat_sound(self, value):
        Sound_System._add_audio_strip(Sound_System.get_bat_sounds(self, bpy.context), value)

    # Bounce
    def get_bounce_sounds(scene, context):
        return Sound_System._create_audio_type_list("Bounce")

    def add_bounce_sound(self, value):
        Sound_System._add_audio_strip(Sound_System.get_bounce_sounds(self, bpy.context), value)

    # Catch
    def get_catch_sounds(scene, context):
        return Sound_System._create_audio_type_list("Catch")

    def add_catch_sound(self, value):
        Sound_System._add_audio_strip(Sound_System.get_catch_sounds(self, bpy.context), value)

    # Clothes
    def get_clothes_sounds(scene, context):
        return Sound_System._create_audio_type_list("Clothes")

    def add_clothes_sound(self, value):
        Sound_System._add_audio_strip(Sound_System.get_clothes_sounds(self, bpy.context), value)

    # Vocals
    def get_vocal_sounds(scene, context):
        return Sound_System._create_audio_type_list("Vocals")

    def add_vocal_sound(self, value):
        Sound_System._add_audio_strip(Sound_System.get_vocal_sounds(self, bpy.context), value)

    # Crowd
    def get_crowd_types(scene, context):
        return Sound_System._create_audio_type_list("Crowd", add_random_option = False)

    def get_crowd_sounds(scene, context):
        crowd_sound_relative_path = os.path.join(
            "Crowd", os.path.basename(bpy.context.scene.vse_select_crowd_type))
        return Sound_System._create_audio_type_list(crowd_sound_relative_path)

    def add_crowd_sound(self, value):
        Sound_System._add_audio_strip(Sound_System.get_crowd_sounds(self, bpy.context), value)

    def _get_base_audio_path():
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "Audio")

    def _create_audio_type_list(audio_type, add_random_option = True):

        audio_type_directory = os.path.join(Sound_System._get_base_audio_path(), audio_type)

        audio_paths = []
        if add_random_option:
            audio_paths.append((Sound_System.RANDOM_IDENTIFIER, "Random", ""))

        for audio_name in os.listdir(audio_type_directory):
            audio_paths.append((os.path.join(audio_type_directory, audio_name), audio_name, ""))

        return audio_paths

    def _add_audio_strip(audio_tuples, index):

        selected_audio_tuple = audio_tuples[index]

        audio_file_path = selected_audio_tuple[0]
        if audio_file_path == Sound_System.RANDOM_IDENTIFIER:
            del audio_tuples[0] # Remove random tuple option
            audio_file_path = random.choice(audio_tuples)[0]

        bpy.ops.sequencer.sound_strip_add(
            filepath = audio_file_path,
            channel = 2,
            frame_start = bpy.context.scene.frame_start)

class Cricket_DataGen_Panel(bpy.types.Panel):
    bl_label = "Cricket Data Generation"
    bl_idname = "VSE_PT_Data_Generation"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'VSE Data Generation'
    
    def draw(self, context):

        if bpy.context.space_data.show_seconds:
            bpy.context.space_data.show_seconds = False

        layout = self.layout
        scn = bpy.context.scene
        
        row = layout.row()
        row.label(text = "Configure & Generate Data Files (.csv)")

        layout.row().separator(factor=3)

        row = layout.row()
        row.label(text = "Start Frame:")
        row.prop(scn, "vse_data_gen_frame_start", text="")
        row.label(text = "End Frame:")
        row.prop(scn, "vse_data_gen_frame_end", text="")

        col = layout.column(align=True)
        col.operator("vse.derive_cutscene_settings", text="Automatically Configure Settings", icon="TIME")

        row = layout.row()
        row.label(text = "Batsman Style:")
        row.prop(scn, "vse_batsman_style", text="")

        row = layout.row()
        row.label(text = "Bowler Style:")
        row.prop(scn, "vse_bowler_style", text="")

        row = layout.row()
        row.label(text = "Action Type:")
        row.prop(scn, "vse_action_type", text="")

        layout.row().separator(factor=3)

        row = layout.row()
        row.label(text = "Time of Action (Frame):")
        row.prop(scn, "vse_time_of_action", text="")

        row = layout.row()
        if (bpy.context.scene.vse_action_type == "B" or
            bpy.context.scene.vse_action_type == "C" or
            bpy.context.scene.vse_action_type == "L"):
                row.label(text = "For a wicket this will be the moment the ball is caught/hits wicket etc…")
        elif (bpy.context.scene.vse_action_type == "4" or
              bpy.context.scene.vse_action_type == "6" or
              bpy.context.scene.vse_action_type == "N4" or
              bpy.context.scene.vse_action_type == "N6"):
                row.label(text = "For runs will be the moment the ball hits the boundary (only applicable for 4, 6, N4, N6)")
        elif (bpy.context.scene.vse_action_type == "1" or
              bpy.context.scene.vse_action_type == "2" or
              bpy.context.scene.vse_action_type == "3" or
              bpy.context.scene.vse_action_type == "N1" or
              bpy.context.scene.vse_action_type == "N2" or
              bpy.context.scene.vse_action_type == "N3"):
                row.label(text = "For runs (1,2,3 and N1, N2, N3) this will be the moment the last run is completed")
        elif (bpy.context.scene.vse_action_type == "0"):
                row.label(text = "For 0 runs the TimeOfAction is the clip duration, Vision would update the UI at the end of the clip.")
        elif (bpy.context.scene.vse_action_type == "W0"):
                row.label(text = "For Wide, this is the time the ball passed the batsman.")
        elif (bpy.context.scene.vse_action_type == "N0"):
                row.label(text = "In the case of “N0” (No Ball with no physical run made) this will be at the time the ball is fielded, for all others its at the time the last run is completed.")
        elif (bpy.context.scene.vse_action_type == "S" or
            bpy.context.scene.vse_action_type == "R"):
                row.label(text = "For Stumped and Runout referrals it will be the time within the referral replay that the batsman is out or not out (in the event of a run being made) – These animation sequences are for phase 2.")

        layout.row().separator(factor=2)

        row = layout.row()
        row.label(text = "Add Audio:")
        layout.prop(scn, "vse_add_bat_sound", text = "Bat")
        layout.prop(scn, "vse_add_bounce_sound", text = "Bounce")
        layout.prop(scn, "vse_add_catch_sound", text = "Catch")
        layout.prop(scn, "vse_add_clothes_sound", text = "Clothes")
        layout.prop(scn, "vse_add_vocal_sound", text = "Vocals")
        row = layout.row()
        row.prop(scn, "vse_select_crowd_type", text = "Crowd")
        row.prop(scn, "vse_add_crowd_sound", text = "")

        layout.row().separator(factor=3)

        row = layout.row()
        row.prop(scn, "vse_data_output_path")

        col = layout.column(align=True)
        col.operator("vse.generate_data", text="Generate Data Files", icon="TIME")


def register():
    bpy.utils.register_class(Cricket_DataGen_Panel)
    bpy.utils.register_class(Generate_Data_Files)
    bpy.utils.register_class(Derive_Settings_from_Name)
    
def unregister():
    bpy.utils.unregister_class(Cricket_DataGen_Panel)
    bpy.utils.unregister_class(Generate_Data_Files)
    bpy.utils.unregister_class(Derive_Settings_from_Name)

def get_frame_start(self):
    return bpy.context.scene.frame_start

def set_frame_start(self, value):
    bpy.context.scene.frame_start = value

def get_frame_end(self):
    return bpy.context.scene.frame_end

def set_frame_end(self, value):
    bpy.context.scene.frame_end = value

def get_vse_time_of_action(self):

    # Create text strip that will be used as a visual node
    if (bpy.context.scene.sequence_editor.sequences_all.get(VSE_ACTION_EVENT_NAME) == None):
        bpy.ops.sequencer.effect_strip_add(
            type ='TEXT',
            frame_start = bpy.context.scene.frame_start,
            frame_end = bpy.context.scene.frame_start + VSE_ACTION_EVENT_SIZE,
            channel = 1)

        number_of_strips = len(bpy.context.scene.sequence_editor.sequences_all.values())
        created_strip = bpy.context.scene.sequence_editor.sequences_all[number_of_strips - 1]
        created_strip.name = VSE_ACTION_EVENT_NAME
        created_strip.font_size = 0
        created_strip.blend_alpha = 0

    time_of_action = bpy.context.scene.sequence_editor.sequences_all.get(VSE_ACTION_EVENT_NAME).frame_start
    if time_of_action > bpy.context.scene.frame_end:
        set_vse_time_of_action(self, bpy.context.scene.frame_end)
    elif time_of_action < bpy.context.scene.frame_start:
        set_vse_time_of_action(self, bpy.context.scene.frame_start)

    return bpy.context.scene.sequence_editor.sequences_all.get(VSE_ACTION_EVENT_NAME).frame_start

def set_vse_time_of_action(self, value):
    bpy.context.scene.sequence_editor.sequences_all.get(VSE_ACTION_EVENT_NAME).frame_start = value
    bpy.context.scene.sequence_editor.sequences_all.get(VSE_ACTION_EVENT_NAME).frame_final_end = value + VSE_ACTION_EVENT_SIZE

def get_output_path(self):
    if self.get("vse_data_output_path", "") == "":
        self["vse_data_output_path"] = bpy.path.abspath("//")

    return self.get("vse_data_output_path", "")

def set_output_path(self, value):
    self["vse_data_output_path"] = value

def assign_control_variables():

    bpy.types.Scene.vse_data_gen_frame_start = (
        bpy.props.IntProperty(name = "Start Frame: ", get = get_frame_start, set = set_frame_start, min = 0))
    bpy.types.Scene.vse_data_gen_frame_end = (
        bpy.props.IntProperty(name = "End Frame: ", get = get_frame_end, set = set_frame_end, min = 0))

    bpy.types.Scene.vse_batsman_style = bpy.props.EnumProperty(items=BATSMAN_STYLE_ITEMS)
    bpy.types.Scene.vse_bowler_style = bpy.props.EnumProperty(items=BOWLER_STYLE_ITEMS)
    bpy.types.Scene.vse_action_type = bpy.props.EnumProperty(items=ACTION_TYPE_ITEMS)

    bpy.types.Scene.vse_time_of_action  = bpy.props.IntProperty(min = 0, get = get_vse_time_of_action, set = set_vse_time_of_action)

    bpy.types.Scene.vse_data_output_path  = ( 
        bpy.props.StringProperty(name = "Output path",
            description = "Where action and sound data files go.\nLeave empty for relative blend directory",
            subtype = "DIR_PATH",
            get = get_output_path,
            set = set_output_path))

    bpy.types.Scene.vse_add_bat_sound = bpy.props.EnumProperty(
        items = Sound_System.get_bat_sounds,
        get = Sound_System.get_default_sound,
        set = Sound_System.add_bat_sound)

    bpy.types.Scene.vse_add_bounce_sound = bpy.props.EnumProperty(
        items = Sound_System.get_bounce_sounds,
        get = Sound_System.get_default_sound,
        set = Sound_System.add_bounce_sound)

    bpy.types.Scene.vse_add_catch_sound = bpy.props.EnumProperty(
        items = Sound_System.get_catch_sounds,
        get = Sound_System.get_default_sound,
        set = Sound_System.add_catch_sound)

    bpy.types.Scene.vse_add_clothes_sound = bpy.props.EnumProperty(
        items = Sound_System.get_clothes_sounds,
        get = Sound_System.get_default_sound,
        set = Sound_System.add_clothes_sound)

    bpy.types.Scene.vse_add_vocal_sound = bpy.props.EnumProperty(
        items = Sound_System.get_vocal_sounds,
        get = Sound_System.get_default_sound,
        set = Sound_System.add_vocal_sound)

    bpy.types.Scene.vse_select_crowd_type = bpy.props.EnumProperty(items = Sound_System.get_crowd_types)

    bpy.types.Scene.vse_add_crowd_sound = bpy.props.EnumProperty(
        items = Sound_System.get_crowd_sounds,
        get = Sound_System.get_default_sound,
        set = Sound_System.add_crowd_sound)


assign_control_variables()
    
