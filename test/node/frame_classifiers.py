from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from dspy.primitives.prediction import Prediction

from src.core.mechanic.duration import Duration, Unit
from src.core.model.entity import EntityKind, ThreatPillar
from src.core.model.entity import EntityData
from src.core.model.threat import Channel
from src.node.frame.approach import ApproachNode
from src.node.frame.duration import DurationNode
from src.node.frame.pillar import PillarNode
from src.node.frame.push import PushNode
from src.node.frame.target import TargetNode
from src.state import GraphState


def _entity(name: str) -> EntityData:
    return EntityData(
        name=name,
        description="d",
        scene_position="here",
        kind=EntityKind.CREATURE,
        id=name.lower(),
    )


def _state(*, entities: list[EntityData] | None = None) -> GraphState:
    return GraphState(
        contested_beat="I strike the foe",
        scene_entities=entities or [],
    )


# ── approach / pillar / push: each maps its one prediction field ────────────
@pytest.mark.asyncio
async def test_approach_maps_attribute():
    node = ApproachNode()
    with patch.object(
        node._program,
        "aforward",
        new=AsyncMock(return_value=Prediction(attribute=Channel.MENS)),
    ):
        assert await node(_state()) == {"attribute": Channel.MENS}


@pytest.mark.asyncio
async def test_pillar_maps_target_pillar():
    node = PillarNode()
    with patch.object(
        node._program,
        "aforward",
        new=AsyncMock(return_value=Prediction(pillar=ThreatPillar.WILLING)),
    ):
        assert await node(_state()) == {"target_pillar": ThreatPillar.WILLING}


@pytest.mark.asyncio
async def test_push_coerces_to_bool():
    node = PushNode()
    with patch.object(
        node._program, "aforward", new=AsyncMock(return_value=Prediction(push=True))
    ):
        assert await node(_state()) == {"push_for_effect": True}


@pytest.mark.asyncio
async def test_duration_maps_unit_to_a_single_rung_span():
    node = DurationNode()
    with patch.object(
        node._program,
        "aforward",
        new=AsyncMock(return_value=Prediction(unit=Unit.SIX_SECONDS)),
    ):
        assert await node(_state()) == {"beat_span": Duration(Unit.SIX_SECONDS)}


@pytest.mark.asyncio
async def test_duration_coerces_a_plain_string_unit():
    # DSPy may hand back the enum's string value; the node coerces to Unit.
    node = DurationNode()
    with patch.object(
        node._program,
        "aforward",
        new=AsyncMock(return_value=Prediction(unit="eight_hours")),
    ):
        assert await node(_state()) == {"beat_span": Duration(Unit.EIGHT_HOURS)}


# ── target: code-derive 0–1 entities, LLM only on 2+ ────────────────────────
@pytest.mark.asyncio
async def test_target_derives_empty_with_no_entities():
    node = TargetNode()
    spy = AsyncMock()
    with patch.object(node._program, "aforward", new=spy):
        assert await node(_state(entities=[])) == {"target_entity": ""}
    spy.assert_not_called()  # no LLM call when there is nothing to target


@pytest.mark.asyncio
async def test_target_derives_single_entity_without_llm():
    node = TargetNode()
    spy = AsyncMock()
    with patch.object(node._program, "aforward", new=spy):
        result = await node(_state(entities=[_entity("Spider")]))
    assert result == {"target_entity": "Spider"}
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_target_classifies_when_ambiguous():
    node = TargetNode()
    fake = AsyncMock(return_value=Prediction(target="  Spider "))
    with patch.object(node._program, "aforward", new=fake):
        result = await node(_state(entities=[_entity("Spider"), _entity("Golem")]))
    assert result == {"target_entity": "Spider"}  # stripped
    fake.assert_awaited_once()
