import pytest
from unittest.mock import AsyncMock, patch
from dspy.primitives.prediction import Prediction

from src.core.model.entity import (
    Danger,
    Disposition,
    EntityKind,
    EntityStance,
    EntityStatus,
    ThreatPillar,
)
from src.core.model.location import EntityData
from src.core.model.message import Message
from src.node.frame.engagement import EngagementNode
from src.state import GraphState


def _creature(
    stance: EntityStance = EntityStance.UNAWARE,
    status: EntityStatus = EntityStatus.ACTIVE,
    disposition: Disposition = Disposition.PREDATORY,
    pillar: ThreatPillar | None = None,
) -> EntityData:
    return EntityData(
        name="Spider",
        description="d",
        scene_position="alcove",
        kind=EntityKind.CREATURE,
        id="s",
        danger=Danger.ELITE,
        disposition=disposition,
        stance=stance,
        status=status,
        broken_pillar=pillar,
        clocks={pillar: 6} if pillar else {},
        returns_when="you are cornered" if pillar else "",
    )


def _state(entity: EntityData, action: str) -> GraphState:
    return GraphState(
        scene_entities=[entity], human_message=Message(role="human", content=action, name="")
    )


def _patch(node: EngagementNode, posture: EntityStance) -> object:
    return patch.object(node._program, "aforward", new=AsyncMock(return_value=Prediction(posture=posture)))


@pytest.mark.asyncio
async def test_noop_when_only_hostile_creatures():
    node = EngagementNode()
    with patch.object(node._program, "aforward", new=AsyncMock()) as called:
        result = await node(_state(_creature(EntityStance.HOSTILE), "I attack"))
    assert result == {}
    called.assert_not_called()


@pytest.mark.asyncio
async def test_aggro_unaware_to_hostile_on_provocation():
    node = EngagementNode()
    with _patch(node, EntityStance.HOSTILE):
        result = await node(_state(_creature(), "I step into the alcove"))
    assert result["scene_entities"][0].stance == EntityStance.HOSTILE
    assert "returned_targets" not in result  # a fresh aggro, not a re-engage


@pytest.mark.asyncio
async def test_aggro_escalates_to_wary():
    node = EngagementNode()
    with _patch(node, EntityStance.WARY):
        result = await node(_state(_creature(), "I creep along the far wall"))
    assert result["scene_entities"][0].stance == EntityStance.WARY


@pytest.mark.asyncio
async def test_unaware_stays_unaware_is_noop():
    node = EngagementNode()
    with _patch(node, EntityStance.UNAWARE):
        result = await node(_state(_creature(), "I tie my boot"))
    assert result == {}


@pytest.mark.asyncio
async def test_suspended_foe_reengages_hostile_and_resets_clock():
    node = EngagementNode()
    foe = _creature(EntityStance.HOSTILE, EntityStatus.SUSPENDED, pillar=ThreatPillar.WILLING)
    with _patch(node, EntityStance.HOSTILE):
        result = await node(_state(foe, "I corner it"))
    entity = result["scene_entities"][0]
    assert entity.status == EntityStatus.ACTIVE
    assert entity.stance == EntityStance.HOSTILE
    assert entity.broken_pillar is None
    assert entity.clocks[ThreatPillar.WILLING] == 0
    assert result["returned_targets"] == ["Spider"]


@pytest.mark.asyncio
async def test_suspended_foe_stays_withdrawn():
    node = EngagementNode()
    foe = _creature(EntityStance.HOSTILE, EntityStatus.SUSPENDED, pillar=ThreatPillar.WILLING)
    with _patch(node, EntityStance.UNAWARE):
        result = await node(_state(foe, "I keep my distance"))
    assert result == {}
