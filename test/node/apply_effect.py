import pytest

from src.core.mechanic.dice import RollResult, RollTier
from src.core.mechanic.harm import WoundPool
from src.core.model.entity import Danger
from src.core.model.location import EntityData
from src.core.model.threat import Channel
from src.node.apply_effect import ApplyEffectNode
from src.state import GraphState


def _spider(filled: int = 0, capacity: int = 6) -> EntityData:
    return EntityData(
        name="Spider",
        description="big",
        scene_position="wall",
        id="sp1",
        danger=Danger.STANDARD,
        threat_channels=frozenset({Channel.CORPUS}),
        wound=WoundPool(capacity=capacity, filled=filled),
    )


def _state(filled: int, tier: RollTier, *, target: str = "Spider", pool: int = 2) -> GraphState:
    return GraphState(
        scene_entities=[_spider(filled)],
        target_entity=target,
        attribute=Channel.CORPUS,
        corpus_rating=pool,
        roll_result=RollResult(dice=(5,), outcome_die=5, tier=tier, zero_pool=False),
    )


@pytest.mark.asyncio
async def test_effect_fills_clock_without_defeat():
    result = await ApplyEffectNode()(_state(0, RollTier.CLEAN))  # standard = 2 segments
    assert result["scene_entities"][0].wound.filled == 2
    assert "defeated_target" not in result


@pytest.mark.asyncio
async def test_effect_defeats_when_clock_fills():
    result = await ApplyEffectNode()(_state(5, RollTier.CLEAN))  # 5 + 2 → capped at 6
    assert result["scene_entities"][0].wound.filled == 6
    assert result["defeated_target"] == "Spider"


@pytest.mark.asyncio
async def test_miss_lands_no_effect():
    result = await ApplyEffectNode()(_state(0, RollTier.BAD))
    assert result == {}


@pytest.mark.asyncio
async def test_no_target_is_noop():
    result = await ApplyEffectNode()(_state(0, RollTier.CLEAN, target=""))
    assert result == {}


@pytest.mark.asyncio
async def test_loose_name_match():
    result = await ApplyEffectNode()(_state(0, RollTier.CLEAN, target="the spider"))
    assert result["scene_entities"][0].wound.filled == 2
