from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ResistAction(StrEnum):
    RESIST = "resist"
    PUSH = "push"
    ENDURE = "endure"


@dataclass(frozen=True)
class HeldScaffold:
    impact_focus: str
    sensory_anchors: tuple[str, ...]
    ambiguity_wedge: tuple[str, ...]
    tension_close: str
    resist_options_text: str


@dataclass(frozen=True)
class FinalScaffold:
    resolutions: tuple[str, ...]
    new_anchors: tuple[str, ...]
    closing_beat: str
    incorporate_player_text: str
