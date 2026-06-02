import pytest

from src.core.mechanic.dice import RollTier
from src.core.mechanic.effect import (
    capacity_for_danger,
    effect_from_tier,
    effect_segments,
    is_defeated,
    pillar_capacity,
    potency_shift,
)
from src.core.model.entity import ThreatPillar
from src.core.mechanic.harm import WoundPool
from src.core.model.entity import Danger
from src.core.model.resolution import Effect


@pytest.mark.parametrize(
    "danger,expected",
    [(Danger.LOW, 1), (Danger.STANDARD, 3), (Danger.ELITE, 6), (Danger.DEADLY, 10)],
)
def test_capacity_for_danger(danger, expected):
    assert capacity_for_danger(danger) == expected


@pytest.mark.parametrize(
    "tier,expected",
    [
        (RollTier.CRIT, Effect.GREAT),
        (RollTier.CLEAN, Effect.STANDARD),
        (RollTier.PARTIAL, Effect.LIMITED),
        (RollTier.BAD, None),
    ],
)
def test_effect_from_tier(tier, expected):
    assert effect_from_tier(tier) == expected


def test_potency_shift_up_when_overpowering():
    # pool 4 vs LOW (rank 1): gap >= 2 → one step up
    assert potency_shift(Effect.STANDARD, 4, Danger.LOW) == Effect.GREAT


def test_potency_shift_down_when_outmatched():
    # pool 0 vs DEADLY (rank 4): gap >= 2 → one step down
    assert potency_shift(Effect.STANDARD, 0, Danger.DEADLY) == Effect.LIMITED


def test_potency_shift_clamps_and_keeps_miss():
    # a miss stays a miss regardless of potency
    assert potency_shift(None, 4, Danger.LOW) is None
    # cannot exceed GREAT
    assert potency_shift(Effect.GREAT, 4, Danger.LOW) == Effect.GREAT


def test_effect_segments():
    assert (
        effect_segments(Effect.GREAT),
        effect_segments(Effect.STANDARD),
        effect_segments(Effect.LIMITED),
        effect_segments(None),
    ) == (3, 2, 1, 0)


def test_is_defeated():
    assert is_defeated(WoundPool(capacity=6, filled=6))
    assert is_defeated(WoundPool(capacity=6, filled=7))
    assert not is_defeated(WoundPool(capacity=6, filled=5))


def test_pillar_capacity_unauthored_is_uniform_from_danger():
    assert pillar_capacity(Danger.ELITE, ThreatPillar.EXISTS) == capacity_for_danger(Danger.ELITE)
    assert pillar_capacity(Danger.ELITE, ThreatPillar.WILLING, {}) == capacity_for_danger(Danger.ELITE)


def test_pillar_capacity_authored_profile_and_immunity():
    profile = {ThreatPillar.EXISTS: 6, ThreatPillar.IN_REACH: 2}
    assert pillar_capacity(Danger.ELITE, ThreatPillar.IN_REACH, profile) == 2
    # a pillar the profile omits is immune (capacity 0)
    assert pillar_capacity(Danger.ELITE, ThreatPillar.WILLING, profile) == 0


@pytest.mark.parametrize(
    "danger,tier,one_shot",
    [
        (Danger.LOW, RollTier.PARTIAL, True),     # weak foe drops on any hit
        (Danger.LOW, RollTier.CLEAN, True),
        (Danger.STANDARD, RollTier.CLEAN, False),  # takes more than one standard hit
        (Danger.DEADLY, RollTier.CRIT, False),     # a real multi-exchange clock
    ],
)
def test_weak_foes_one_shot_tough_foes_do_not(danger, tier, one_shot):
    # neutral potency (pool == danger rank) so only the tuning is under test
    pool = {Danger.LOW: 1, Danger.STANDARD: 2, Danger.ELITE: 3, Danger.DEADLY: 4}[danger]
    segments = effect_segments(potency_shift(effect_from_tier(tier), pool, danger))
    assert (segments >= capacity_for_danger(danger)) == one_shot
