from __future__ import annotations

from src.core.model.entity import Danger, EntityData, EntityKind, EntityStance, EntityStatus
from src.graph.routers import FRAME_BRANCHES, fan_out_frame_and_threats
from src.state import GraphState


def _hostile(name: str) -> EntityData:
    return EntityData(
        name=name,
        description="d",
        scene_position="here",
        kind=EntityKind.CREATURE,
        id=name.lower(),
        danger=Danger.STANDARD,
        stance=EntityStance.HOSTILE,
        status=EntityStatus.ACTIVE,
    )


def test_fan_out_covers_framing_then_threats():
    state = GraphState(contested_beat="I strike", scene_entities=[_hostile("Spider")])
    sends = fan_out_frame_and_threats(state)
    targets = [s.node for s in sends]

    # All four discrete framing classifiers fan out, exactly once each...
    assert targets[: len(FRAME_BRANCHES)] == list(FRAME_BRANCHES)
    # ...alongside the threat branches (the hostile creature + the environment).
    assert targets[len(FRAME_BRANCHES) :] == ["classify_threat", "classify_threat"]


def test_framing_sends_carry_full_state():
    state = GraphState(contested_beat="I strike", scene_entities=[_hostile("Spider")])
    frame_sends = fan_out_frame_and_threats(state)[: len(FRAME_BRANCHES)]
    # Each framing branch gets a full state copy (a plain dict — the native
    # TypedDict channel payload), so the node can read contested_beat off it.
    for s in frame_sends:
        assert isinstance(s.arg, dict)
        assert s.arg["contested_beat"] == "I strike"
