from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ResistAction(StrEnum):
    RESIST = "resist"
    PUSH = "push"
    ENDURE = "endure"


class HeldScaffold(BaseModel):
    model_config = ConfigDict(frozen=True)

    impact_focus: str
    sensory_anchors: tuple[str, ...]
    ambiguity_wedge: tuple[str, ...]
    tension_close: str
    resist_options_text: str


class FinalScaffold(BaseModel):
    model_config = ConfigDict(frozen=True)

    resolutions: tuple[str, ...]
    new_anchors: tuple[str, ...]
    closing_beat: str
    incorporate_player_text: str
