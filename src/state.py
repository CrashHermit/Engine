import operator
from typing import Annotated

from pydantic import BaseModel, Field

from src.core.model.message import Message
from src.core.model.resist import FinalScaffold, HeldScaffold, ResistAction
from src.core.model.threat import Channel, ThreatType
from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.scaling import Outcome, Position
from src.core.mechanic.dice import RollResult


class GraphState(BaseModel):
    message_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    intent_alignment_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    human_message: Message | None = None
    ai_message: Message | None = None
    question: str | None = None
    is_intent_alignment_achieved: bool | None = None
    needs_roll: bool | None = None
    lead_up: str | None = None
    contested_beat: str | None = None
    deferred_tail: str | None = None
    location_name: str = ""
    location_description: str = ""
    entities_at_location: list[str] = Field(default_factory=list)
    character_name: str = ""
    character_description: str = ""
    attribute: Channel | None = None
    threat_type: ThreatType | None = None
    magnitude: Magnitude | None = None
    threat_channel: Channel | None = None
    corpus_rating: int = 0
    mens_rating: int = 0
    anima_rating: int = 0

    position: Position = Position.RISKY

    roll_result: RollResult | None = None
    outcome: Outcome | None = None

    # Narration pipeline
    narration_directive: str | None = None
    anchors: str | None = None
    prior_prose: str | None = None
    held_scaffold: HeldScaffold | None = None
    final_scaffold: FinalScaffold | None = None

    # Resistance / push turn
    resist_response: str | None = None
    resist_action: ResistAction | None = None
    resist_flavor: str | None = None
    resist_roll_result: RollResult | None = None

    # Per-turn economy (initialised from persisted character state by the TUI)
    stress: int = 0
    trauma: int = 0
    # Set by resist_roll when a stress overflow converts to trauma (and, at the
    # trauma cap, the character is lost). Surfaced by the coordinator post-turn.
    trauma_gained: bool = False
    character_lost: bool = False
