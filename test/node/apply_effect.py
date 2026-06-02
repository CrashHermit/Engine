import pytest

from src.core.mechanic.dice import RollResult, RollTier
from src.core.model.entity import Danger, EntityKind, EntityStatus, ThreatPillar
from src.core.model.location import EntityData
from src.core.model.threat import Channel
from src.node.apply_effect import ApplyEffectNode
from src.state import GraphState


def _spider(clocks: dict[ThreatPillar, int] | None = None, danger: Danger = Danger.STANDARD) -> EntityData:
    return EntityData(
        name="Spider",
        description="big",
        scene_position="wall",
        kind=EntityKind.CREATURE,
        id="sp1",
        danger=danger,
        threat_channels=frozenset({Channel.CORPUS}),
        clocks=clocks or {},
    )


def _state(
    entity: EntityData,
    tier: RollTier,
    *,
    pillar: ThreatPillar = ThreatPillar.EXISTS,
    target: str = "Spider",
    pool: int = 2,
) -> GraphState:
    return GraphState(
        scene_entities=[entity],
        target_entity=target,
        target_pillar=pillar,
        attribute=Channel.CORPUS,
        corpus_rating=pool,
        roll_result=RollResult(dice=(6,), outcome_die=6, tier=tier, zero_pool=False),
    )


@pytest.mark.asyncio
async def test_fills_targeted_pillar_clock():
    # STANDARD danger => capacity 3; CLEAN => 2 segments on EXISTS.
    result = await ApplyEffectNode()(_state(_spider(), RollTier.CLEAN))
    spider = result["scene_entities"][0]
    assert spider.clocks[ThreatPillar.EXISTS] == 2
    assert spider.status == EntityStatus.ACTIVE
    assert "defeated_target" not in result and "suspended_target" not in result


@pytest.mark.asyncio
async def test_breaking_exists_destroys_and_defeats():
    # already 1/3 on EXISTS; CLEAN (2) fills it -> GONE + defeated_target
    result = await ApplyEffectNode()(_state(_spider({ThreatPillar.EXISTS: 1}), RollTier.CLEAN))
    spider = result["scene_entities"][0]
    assert spider.status == EntityStatus.GONE
    assert result["defeated_target"] == "Spider"
    assert "resolution_outcome" in result


@pytest.mark.asyncio
async def test_breaking_willing_suspends_not_kills():
    # fill the WILLING pillar instead -> SUSPENDED, no defeat (non-lethal)
    s = _state(_spider({ThreatPillar.WILLING: 1}), RollTier.CLEAN, pillar=ThreatPillar.WILLING)
    s.attribute = Channel.ANIMA
    s.anima_rating = 2
    result = await ApplyEffectNode()(s)
    spider = result["scene_entities"][0]
    assert spider.status == EntityStatus.SUSPENDED
    assert spider.broken_pillar == ThreatPillar.WILLING
    assert spider.returns_when  # a return condition was recorded for Phase 2
    assert result["suspended_target"] == "Spider"
    assert "defeated_target" not in result


@pytest.mark.asyncio
async def test_pillars_are_independent_clocks():
    # progress on EXISTS does not advance WILLING
    spider = _spider({ThreatPillar.EXISTS: 2})
    result = await ApplyEffectNode()(_state(spider, RollTier.PARTIAL, pillar=ThreatPillar.WILLING, pool=2))
    out = result["scene_entities"][0]
    assert out.clocks[ThreatPillar.EXISTS] == 2  # untouched
    assert out.clocks[ThreatPillar.WILLING] == 1  # PARTIAL = 1 segment


@pytest.mark.asyncio
async def test_miss_lands_no_effect():
    assert await ApplyEffectNode()(_state(_spider(), RollTier.BAD)) == {}


@pytest.mark.asyncio
async def test_object_target_takes_no_clock_damage():
    lantern = EntityData(
        name="Dead Lantern", description="rusted", scene_position="ceiling",
        kind=EntityKind.OBJECT, id="ln1",
    )
    state = GraphState(
        scene_entities=[lantern], target_entity="Dead Lantern", target_pillar=ThreatPillar.EXISTS,
        attribute=Channel.CORPUS, corpus_rating=2,
        roll_result=RollResult(dice=(6,), outcome_die=6, tier=RollTier.CLEAN, zero_pool=False),
    )
    assert await ApplyEffectNode()(state) == {}
