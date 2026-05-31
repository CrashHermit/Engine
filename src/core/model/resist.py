from enum import StrEnum

from pydantic import BaseModel


class ResistAction(StrEnum):
    RESIST = "resist"
    PUSH = "push"
    ENDURE = "endure"


class HeldScaffold(BaseModel):
    impact_focus: str
    sensory_anchors: str
    ambiguity_wedge: str
    tension_close: str
    resist_options: str
