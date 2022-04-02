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

        return new_action

    def _create_new_action(self) -> Action:
        """test"""

        if self.parameters.action  != None:
            if len(self.parameters.action.fcurves[0].keyframe_points) <= 1:
                self.parameters.OT_source_operator.report(
                    {"INFO"},
                    "Final frame not present, a dummy frame will be added")

        else:
            self.parameters.OT_source_operator.report(
                {"INFO"},
                "No keyframes present, dummy keyframes will be added")

        return print("_create_new_action")

    def _store_animation(self, action: Action) -> None:
        """test"""
        return print("_store_animation")


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
    animation_action =  animation_creator.create()

    return animation_action
