import pytest

from src.core.mechanic.dice import RollTier
from src.core.mechanic.effect import (
    capacity_for_danger,
    effect_from_tier,
    effect_segments,
    is_defeated,
    potency_shift,
)
from src.core.mechanic.harm import WoundPool
from src.core.model.entity import Danger
from src.core.model.resolution import Effect


@pytest.mark.parametrize(
    "danger,expected",
    [(Danger.LOW, 4), (Danger.STANDARD, 6), (Danger.ELITE, 8), (Danger.DEADLY, 10)],
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
