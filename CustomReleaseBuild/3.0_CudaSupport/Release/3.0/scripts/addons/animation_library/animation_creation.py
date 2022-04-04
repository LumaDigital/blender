import bpy
from bpy.types import (
    Action,
    Context,
    FCurve,
    Keyframe,
    Operator)

from typing import Optional#, FrozenSet, Set, Union, Iterable, cast

import dataclasses

@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class AnimationCreationParameters:
    OT_source_operator: Operator
    context_object: bpy.types.Object
    current_action: Optional[Action]
    start_frame: float
    end_frame: float
    asset_name: str

@dataclasses.dataclass(unsafe_hash=True)
class AnimationActionCreator:
    """test"""

    # If the incorrect number of keyframes is present in the animation data, dummy keyframes
    # are added with this distance inbetween the start and end frame for clear readibility 
    DUMMY_FRAMES_DISTANCE = 5

    parameters: AnimationCreationParameters

    def create_animation_action(self) -> Action:
        """test"""

        new_action = bpy.data.actions.new(self.parameters.asset_name)
        current_action = self.parameters.current_action
        if current_action != None:

            # Add end frame to current animation data if not present so the user
            # can create an animation with the current single frame pose if desired
            if len(current_action.fcurves[0].keyframe_points) <= 1:

                self.parameters.OT_source_operator.report(
                    {"INFO"},
                    "Final frame not present, a dummy frame will be added")

                current_action.fcurves[0].keyframe_points.insert(
                    current_action.fcurves[0].keyframe_points[0].co[0] + self.DUMMY_FRAMES_DISTANCE, # x value of keyframe coordinates + distance
                    0)

            new_action = current_action.copy()

            # Attach action to force the timeline to update with the new key
            self.parameters.context_object.animation_data.action = new_action

        else:
            self.parameters.OT_source_operator.report(
                {"INFO"},
                "No keyframes present, dummy keyframes will be added")

            fcurve = new_action.fcurves.new(
                "AnimationActionCreator",
                index = 0,
                action_group = "Animation Actions") # TODO: Look into what data paths are and pass the correct path

            fcurve.keyframe_points.insert(
                1,
                0)
            fcurve.keyframe_points.insert(
                self.DUMMY_FRAMES_DISTANCE,
                0)

            # Assign action
            self.parameters.context_object.animation_data_create()
            self.parameters.context_object.animation_data.action = new_action

        return new_action

def create_animation_asset(
    OT_source_operator: Operator,
    context: Context,
    asset_name: str,
    start_frame: int,
    end_frame: int) -> Optional[Action]:
    """Test test"""

    parameters = AnimationCreationParameters(
        OT_source_operator,
        context.object,
        getattr(context.object.animation_data, "action", None),
        start_frame,
        end_frame,
        asset_name)

    animation_creator = AnimationActionCreator(parameters)
    animation_action =  animation_creator.create_animation_action()
    animation_action.asset_mark()
    animation_action.asset_generate_preview()

    return animation_action
