import pytest
from unittest.mock import AsyncMock, patch
from dspy.primitives.prediction import Prediction

from src.core.model.entity import Danger, EntityKind, EntityStatus, ThreatPillar
from src.core.model.location import EntityData
from src.core.model.message import Message
from src.node.reengage import ReengageNode
from src.state import GraphState


def _foe(status: EntityStatus, pillar: ThreatPillar | None = None) -> EntityData:
    return EntityData(
        name="Spider",
        description="d",
        scene_position="p",
        kind=EntityKind.CREATURE,
        id="x",
        danger=Danger.ELITE,
        status=status,
        broken_pillar=pillar,
        clocks={pillar: 6} if pillar else {},
        returns_when="you are cornered" if pillar else "",
    )


def _state(entity: EntityData, action: str) -> GraphState:
    return GraphState(
        scene_entities=[entity],
        human_message=Message(role="human", content=action, name=""),
    )


@pytest.mark.asyncio
async def test_noop_when_nothing_suspended():
    # No LLM call, empty update.
    node = ReengageNode()
    with patch.object(node._program, "aforward", new=AsyncMock()) as called:
        result = await node(_state(_foe(EntityStatus.ACTIVE), "I wait"))
    assert result == {}
    called.assert_not_called()


@pytest.mark.asyncio
async def test_reactivates_when_judge_says_return():
    node = ReengageNode()
    state = _state(_foe(EntityStatus.SUSPENDED, ThreatPillar.WILLING), "I corner it")
    with patch.object(node._program, "aforward", new=AsyncMock(return_value=Prediction(returns=True))):
        result = await node(state)
    entity = result["scene_entities"][0]
    assert entity.status == EntityStatus.ACTIVE
    assert entity.broken_pillar is None
    assert entity.clocks[ThreatPillar.WILLING] == 0  # rallied — pillar reset
    assert result["returned_targets"] == ["Spider"]


@pytest.mark.asyncio
async def test_stays_suspended_when_judge_says_no():
    node = ReengageNode()
    state = _state(_foe(EntityStatus.SUSPENDED, ThreatPillar.WILLING), "I tie my boot")
    with patch.object(node._program, "aforward", new=AsyncMock(return_value=Prediction(returns=False))):
        result = await node(state)
    assert result == {}
