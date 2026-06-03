"""Control-flow contract for the resolution graph.

Every conditional edge / dynamic fan-out in the turn pipeline lives here, named
and documented, so the graph's *shape* can be read in one place rather than
inferred from imperative `add_conditional_edges` calls. These are pure functions
of `GraphState`; the builder in `resolution_graph.py` only wires them.
"""

from langgraph.types import Send

from src.core.model.entity import EntityKind, EntityStance, EntityStatus
from src.state import GraphState


def _has_active_hostile(state: GraphState) -> bool:
    return any(
        e.status == EntityStatus.ACTIVE
        and e.kind == EntityKind.CREATURE
        and e.stance == EntityStance.HOSTILE
        for e in state.scene_entities
    )


def route_by_roll_gate(state: GraphState) -> str:
    # Contested → roll path. Otherwise, if a hostile creature is present it acts
    # (world-acts ambush); only a truly quiet scene gets the plain mundane path.
    if state.needs_roll:
        return "segmenter"
    return "ambush" if _has_active_hostile(state) else "mundane"


def fan_out_ambush(state: GraphState) -> list[Send]:
    """World-acts fan-out: one classify branch per ACTIVE hostile creature (the
    things actually striking). No environment — nothing the player did provoked
    it; the creatures act on their own."""
    return [
        Send(
            "classify_threat",
            state.model_copy(update={"classify_source": e.name, "classify_entity": e}),
        )
        for e in state.scene_entities
        if e.status == EntityStatus.ACTIVE
        and e.kind == EntityKind.CREATURE
        and e.stance == EntityStance.HOSTILE
    ]


def route_after_gather(state: GraphState) -> str:
    # World-acts threats land at full (ambush_scale); a player action scales
    # them by the roll (dice_scale).
    return "ambush_scale" if state.is_ambush else "dice_scale"


def fan_out_threats(state: GraphState) -> list[Send]:
    """One classify branch per candidate source: every entity present, plus the
    environment. Each Send carries a full GraphState copy with only its own
    source/entity set — LangGraph does NOT coerce a Send payload into the
    pydantic state schema, so passing a dict would hand the branch a bare dict
    (breaking LoggedNode.model_dump and the node's attribute access). model_copy
    keeps the branch typed and preserves the full turn context."""
    # Only ACTIVE sources threaten; a CREATURE must also be HOSTILE (the aggro
    # gate). Objects threaten environmentally regardless of stance.
    sends = [
        Send(
            "classify_threat",
            state.model_copy(update={"classify_source": e.name, "classify_entity": e}),
        )
        for e in state.scene_entities
        if e.status == EntityStatus.ACTIVE
        and (e.kind != EntityKind.CREATURE or e.stance == EntityStance.HOSTILE)
    ]
    sends.append(
        Send(
            "classify_threat",
            state.model_copy(update={"classify_source": "environment", "classify_entity": None}),
        )
    )
    return sends


FRAME_BRANCHES = ("approach", "pillar", "push", "target")


def fan_out_frame_and_threats(state: GraphState) -> list[Send]:
    """Off the segmenter, fan the whole roll prep out in parallel: the four
    discrete framing classifiers (approach/pillar/push/target — each reads the
    same contested beat) plus one classify branch per candidate threat source.
    Both arms rejoin at gather_threats — same superstep — so framing overlaps
    the threat enumeration instead of running before it, and the downstream roll
    fires once. Each Send carries a full typed state copy (see fan_out_threats on
    why model_copy, not a bare dict)."""
    sends = [Send(branch, state.model_copy()) for branch in FRAME_BRANCHES]
    sends.extend(fan_out_threats(state))
    return sends


def route_by_significance(state: GraphState) -> str:
    return "held_planner" if state.landed_threats else "final_planner"


def route_after_narrator(state: GraphState) -> str:
    # Cohesive held setup → begin the resist cycle. Mundane/avoided → close.
    if (
        state.held_scaffold is not None
        and state.final_scaffold is None
        and state.resist_cursor == 0
    ):
        return "resist_offer"
    return "turn_close"


def route_after_resolution(state: GraphState) -> str:
    # Per-threat resolution line just narrated. Stop on permadeath; otherwise
    # offer the next landed threat, else close.
    if state.character_lost:
        return "turn_close"
    if state.resist_cursor < len(state.resist_queue):
        return "resist_offer"
    return "turn_close"
