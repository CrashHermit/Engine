import operator
from typing import Annotated

from pydantic import BaseModel, Field

from src.core.model.message import Message


class GraphState(BaseModel):
    message_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    intent_alignment_history: Annotated[list[Message], operator.add] = Field(default_factory=list)
    human_message: Message | None = None
    ai_message: Message | None = None
    question: str | None = None
    is_intent_alignment_achieved: bool | None = None
    location_name: str = ""
    location_description: str = ""
    entities_at_location: list[str] = Field(default_factory=list)
    character_name: str = ""
    character_description: str = ""

    # --- character ratings (0-4), carried in for code-side dice rolls (#8/#20) ---
    corpus: int = 0
    mens: int = 0
    anima: int = 0

    # --- resolution pipeline (decisions #7, #9, #15-17) ---
    needs_roll: bool | None = None          # roll-gate: danger + uncertainty?
    lead_up: str = ""                       # segmenter: mundane setup before the beat
    contested_beat: str = ""                # segmenter: the single rolled action
    deferred_tail: str = ""                 # segmenter: everything past the beat (held, #10)
    # framing (stubbed in Phase 1, real classifiers in Phase 2)
    attribute: str | None = None            # corpus / mens / anima
    effect: str = ""                        # limited / standard / great
    threat_type: str | None = None          # harm / complication / ...
    threat_channel: str | None = None       # which attribute resists it
    base_magnitude: int | None = None       # threat magnitude before the roll (0-4)
    # roll + scaling result (deterministic code)
    roll_dice: list[int] = Field(default_factory=list)
    roll_tier: str | None = None            # crit / clean / partial / bad
    landed_magnitude: int | None = None     # what actually lands, after scaling
    outcome_avoided: bool | None = None     # cleanly avoided (6 / crit)
    outcome_crit: bool | None = None        # a benefit is owed
