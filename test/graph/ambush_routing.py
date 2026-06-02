from src.core.model.entity import Danger, Disposition, EntityKind, EntityStance, EntityStatus
from src.core.model.location import EntityData
from src.graph.resolution_graph import (
    _fan_out_ambush,
    _route_after_gather,
    _route_by_roll_gate,
)
from src.state import GraphState


def _creature(stance: EntityStance, status: EntityStatus = EntityStatus.ACTIVE) -> EntityData:
    return EntityData(
        name="Spider", description="d", scene_position="alcove", kind=EntityKind.CREATURE, id="s",
        danger=Danger.ELITE, disposition=Disposition.PREDATORY, stance=stance, status=status,
    )


def _object() -> EntityData:
    return EntityData(name="Rubble", description="loose", scene_position="ceiling",
                      kind=EntityKind.OBJECT, id="r")


def test_contested_turn_routes_to_roll_path():
    state = GraphState(needs_roll=True, scene_entities=[_creature(EntityStance.HOSTILE)])
    assert _route_by_roll_gate(state) == "segmenter"


def test_mundane_with_hostile_creature_routes_to_ambush():
    state = GraphState(needs_roll=False, scene_entities=[_creature(EntityStance.HOSTILE)])
    assert _route_by_roll_gate(state) == "ambush"


def test_mundane_with_only_unaware_creature_routes_to_mundane():
    state = GraphState(needs_roll=False, scene_entities=[_creature(EntityStance.UNAWARE)])
    assert _route_by_roll_gate(state) == "mundane"


def test_mundane_with_only_objects_routes_to_mundane():
    # an object never ambushes (no agency)
    state = GraphState(needs_roll=False, scene_entities=[_object()])
    assert _route_by_roll_gate(state) == "mundane"


def test_suspended_hostile_does_not_ambush():
    state = GraphState(
        needs_roll=False,
        scene_entities=[_creature(EntityStance.HOSTILE, EntityStatus.SUSPENDED)],
    )
    assert _route_by_roll_gate(state) == "mundane"


def test_ambush_fan_out_covers_only_hostile_creatures():
    state = GraphState(scene_entities=[
        _creature(EntityStance.HOSTILE), _creature(EntityStance.UNAWARE), _object(),
    ])
    sources = [s.arg.classify_source for s in _fan_out_ambush(state)]
    assert sources == ["Spider"]  # the hostile one only; no environment, no object


def test_gather_split_by_ambush_flag():
    assert _route_after_gather(GraphState(is_ambush=True)) == "ambush_scale"
    assert _route_after_gather(GraphState(is_ambush=False)) == "dice_scale"
