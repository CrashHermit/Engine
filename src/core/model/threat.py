import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from src.core.mechanic.dice import RollResult
from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.scaling import Outcome, Position
from src.core.model.resist import ResistAction


class Channel(StrEnum):
    CORPUS = "corpus"
    MENS = "mens"
    ANIMA = "anima"


class ThreatType(StrEnum):
    HARM = "harm"
    COMPLICATION = "complication"
    WORSE_POSITION = "worse_position"
    LOST_OPPORTUNITY = "lost_opportunity"
    FAILURE_OF_GOAL = "failure_of_goal"


class ThreatMagnitudeLevel(StrEnum):
    """The string ladder the LLM classifiers parse into. Distinct from the
    mechanical Magnitude(IntEnum): the names line up (MINOR/STANDARD/SEVERE/
    FATAL) so `Magnitude[level]` converts one to the other."""

    MINOR = "MINOR"
    STANDARD = "STANDARD"
    SEVERE = "SEVERE"
    FATAL = "FATAL"


@dataclass
class Threat:
    """One landed (or candidate) consequence from a single source. Offense and
    defense are decoupled: the action roll lands the player's effect on the
    target, while every Threat gets its OWN independent defense roll on its own
    channel (which attribute resists it) — that per-threat tier scales it via
    scale_threat. defense_roll/outcome/resist_* fill in as it moves through
    dice_scale and the resist cycle."""

    source: str  # entity name, or "environment"
    type: ThreatType
    channel: Channel
    magnitude: Magnitude  # already capped by source danger
    position: Position
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    defense_roll: RollResult | None = None  # this threat's own channel roll
    outcome: Outcome | None = None
    resist_action: ResistAction | None = None
    resist_flavor: str = ""
    resist_roll: RollResult | None = None
    resisted: bool = False