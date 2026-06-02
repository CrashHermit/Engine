import operator
from typing import Annotated

from pydantic import BaseModel, Field

from src.core.mechanic.dice import RollResult
from src.core.mechanic.magnitude import Magnitude
from src.core.model.entity import Danger, ThreatPillar  # noqa: F401  (Danger kept for callers)
from src.core.model.location import EntityData
from src.core.model.message import Message
from src.core.model.resist import FinalScaffold, HeldScaffold, ResistAction
from src.core.model.threat import Channel, Threat


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
    # Rendered strings for prompts AND the structured spine for enumeration/caps.
    entities_at_location: list[str] = Field(default_factory=list)
    scene_entities: list[EntityData] = Field(default_factory=list)

    character_name: str = ""
    character_description: str = ""
    corpus_rating: int = 0
    mens_rating: int = 0
    anima_rating: int = 0

    # The single action: which attribute it rolls, its target/pillar, and roll.
    attribute: Channel | None = None
    target_entity: str = ""  # name of the entity the action is directed at
    target_pillar: ThreatPillar | None = None  # which condition the action attacks
    roll_result: RollResult | None = None

    # ── Effect-on-target ─────────────────────────────────────────────────
    # apply_effect fills the targeted pillar's clock (carried inside
    # scene_entities). Breaking EXISTS names a defeated_target (removed); any
    # other pillar names a suspended_target (out of the scene, may return).
    # resolution_outcome tells the narrator how to frame the result.
    defeated_target: str = ""
    suspended_target: str = ""
    resolution_outcome: str = ""
    # Suspended creatures that re-engaged this turn (durability / Phase 2).
    returned_targets: list[str] = Field(default_factory=list)
    reengagement_note: str = ""

    # ── Threats ──────────────────────────────────────────────────────────
    # Per-source classify branches (Send fan-out) append here; gather_threats
    # copies into `threats` (plain, overwritten by dice_scale / resist).
    pending_threats: Annotated[list[Threat], operator.add] = Field(default_factory=list)
    threats: list[Threat] = Field(default_factory=list)
    # Transient per-branch carriers for the Send fan-out (set per invocation).
    classify_source: str = ""
    classify_entity: EntityData | None = None

    # ── Resist cycle ─────────────────────────────────────────────────────
    # Stable iteration order: ids of the threats that landed, captured once at
    # held time so resisting one to magnitude 0 can't shift the cursor.
    resist_queue: list[str] = Field(default_factory=list)
    resist_cursor: int = 0
    resist_response: str | None = None       # transient: latest player reply
    resist_action: ResistAction | None = None  # transient: parsed this iteration
    resist_flavor: str | None = None

    # ── Narration pipeline ───────────────────────────────────────────────
    narration_directive: str | None = None
    anchors: str | None = None
    prior_prose: str | None = None
    held_scaffold: HeldScaffold | None = None
    final_scaffold: FinalScaffold | None = None

    # ── Per-run economy ──────────────────────────────────────────────────
    stress: int = 0
    trauma: int = 0
    trauma_gained: bool = False
    character_lost: bool = False

    # ── Derived helpers ──────────────────────────────────────────────────
    @property
    def landed_threats(self) -> list[Threat]:
        return [
            t
            for t in self.threats
            if t.outcome is not None and t.outcome.landed_magnitude >= Magnitude.MINOR
        ]

    @property
    def current_threat(self) -> Threat | None:
        if 0 <= self.resist_cursor < len(self.resist_queue):
            tid = self.resist_queue[self.resist_cursor]
            return next((t for t in self.threats if t.id == tid), None)
        return None