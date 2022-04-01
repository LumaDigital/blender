import bpy
from bpy.types import (
    Action,
    Context,
    FCurve,
    Keyframe)

from typing import Optional#, FrozenSet, Set, Union, Iterable, cast

import dataclasses

@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class AnimationCreationParameters:
    context_object: bpy.types.Object
    action: Optional[Action]
    start_frame: float
    end_frame: float
    asset_name: str

@dataclasses.dataclass(unsafe_hash=True)
class AnimationActionCreator:
    """test"""

    parameters: AnimationCreationParameters

    def create(self) -> Optional[Action]:
        """test"""

        new_action = self._create_new_action()
        self._store_animation(new_action)

        #if len(dst_action.fcurves) == 0:
        #    bpy.data.actions.remove(new_action)
        #    return None

        return new_action

    def _create_new_action(self) -> Action:
        """test"""
        #dst_action = bpy.data.actions.new(self.parameters.asset_name)
        print ("dst_action_frame_range: " + str(dst_action.frame_range))
        #print ("frame_range: " + str(self.parameters.action.frame_range[1]))

        return print("_create_new_action")

    def _store_animation(self, action: Action) -> None:
        """test"""
        return print("_store_animation")


def create_animation_asset(
    context: Context,
    asset_name: str,
    start_frame: int,
    end_frame: int) -> Optional[Action]:
    """Test test"""

    parameters = AnimationCreationParameters(
        context.object,
        getattr(context.object.animation_data, "action", None),
        start_frame,
        end_frame,
        asset_name)

    animation_creator = AnimationActionCreator(parameters)
    animation_action =  animation_creator.create()

    return "lol"
