from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from src.core.mechanic.dice import RollResult
from src.core.mechanic.duration import Duration
from src.core.mechanic.magnitude import Magnitude
from src.core.model.action import ActionIntent
from src.core.model.entity import ThreatPillar
from src.core.model.location import EntityData
from src.core.model.message import Message
from src.core.model.resist import FinalScaffold, HeldScaffold, ResistAction
from src.core.model.threat import Channel, Threat


class GraphState(TypedDict, total=False):
    """Hold the turn blackboard as a LangGraph TypedDict.

    Every key is a channel, so a node reads with ``state.get(...)`` (unwritten
    channels are simply absent) and writes by returning a partial dict.
    ``total=False`` mirrors that — no key is guaranteed present until something
    sets it. The two ``*_history`` lists and ``pending_threats`` are reducer
    channels (append on update); everything else is last-value.
    """

    message_history: Annotated[list[Message], operator.add]
    intent_alignment_history: Annotated[list[Message], operator.add]
    human_message: Message | None
    ai_message: Message | None
    question: str | None
    is_intent_alignment_achieved: bool | None
    needs_roll: bool | None
    lead_up: str | None
    contested_beat: str | None

    location_name: str
    scene_entities: list[EntityData]

    character_name: str
    # Attribute dice pools keyed by channel (corpus/mens/anima). Seeded by the
    # coordinator; read via pool_for().
    ratings: dict[Channel, int]

    # The single action: which attribute it rolls, its target/pillar, and roll.
    attribute: Channel | None
    target_entity: str  # name of the entity the action is directed at
    target_pillar: ThreatPillar | None  # which condition the action attacks
    push_for_effect: bool  # spend stress for +1 effect segment on the target
    roll_result: RollResult | None

    # ── World clock ──────────────────────────────────────────────────────
    # Seeded from the world clock (TimeService.now) at turn start; how much
    # fictional time this beat spans (set by the duration classifier when wired
    # — until then the coordinator advances a default six_seconds per closed turn).
    elapsed_ticks: int
    beat_span: Duration | None

    # ── Effect-on-target ─────────────────────────────────────────────────
    # apply_effect fills the targeted pillar's clock (carried inside
    # scene_entities). Breaking EXISTS names a defeated_target (removed); any
    # other pillar names a suspended_target (out of the scene, may return).
    # resolution_outcome tells the narrator how to frame the result.
    defeated_target: str
    suspended_target: str
    resolution_outcome: str
    # Creatures the engagement check re-engaged this turn (suspended -> active).
    returned_targets: list[str]
    # Narration hint for posture changes this turn (aggro + re-engage).
    engagement_note: str

    # ── Threats ──────────────────────────────────────────────────────────
    # Per-source classify branches (Send fan-out) append here; gather_threats
    # copies into `threats` (plain, overwritten by dice_scale / resist).
    pending_threats: Annotated[list[Threat], operator.add]
    threats: list[Threat]
    # World-acts turn: a hostile creature strikes on a non-contested turn. No
    # player action roll — threats land at full magnitude; the player resists.
    is_ambush: bool
    # Transient per-branch carriers for the Send fan-out (set per invocation).
    classify_source: str
    classify_entity: EntityData | None

    # ── Resist cycle ─────────────────────────────────────────────────────
    # Stable iteration order: ids of the threats that landed, captured once at
    # held time so resisting one to magnitude 0 can't shift the cursor.
    resist_queue: list[str]
    resist_cursor: int
    resist_response: str | None  # transient: latest player reply
    resist_action: ResistAction | None  # transient: parsed this iteration
    resist_flavor: str | None

    # ── Narration pipeline ───────────────────────────────────────────────
    narration_directive: str | None
    anchors: str | None
    prior_prose: str | None
    held_scaffold: HeldScaffold | None
    final_scaffold: FinalScaffold | None

    # ── Per-run economy ──────────────────────────────────────────────────
    stress: int
    trauma: int
    trauma_gained: bool
    character_lost: bool


# ── Derived helpers (free functions; a TypedDict carries no behavior) ─────
def action_intent(state: GraphState) -> ActionIntent:
    """Return the single action as one cohesive value (view over the flat fields)."""
    return ActionIntent(
        attribute=state.get("attribute"),
        target=state.get("target_entity", ""),
        pillar=state.get("target_pillar") or ThreatPillar.EXISTS,
        push=state.get("push_for_effect", False),
    )


def pool_for(state: GraphState, channel: Channel | None) -> int:
    """Dice pool for an attribute channel (0 if unknown)."""
    if channel is None:
        return 0
    return state.get("ratings", {}).get(channel, 0)


def landed_threats(state: GraphState) -> list[Threat]:
    return [
        t
        for t in state.get("threats", [])
        if t.outcome is not None and t.outcome.landed_magnitude >= Magnitude.MINOR
    ]


def current_threat(state: GraphState) -> Threat | None:
    queue = state.get("resist_queue", [])
    cursor = state.get("resist_cursor", 0)
    if 0 <= cursor < len(queue):
        tid = queue[cursor]
        return next((t for t in state.get("threats", []) if t.id == tid), None)
    return None
