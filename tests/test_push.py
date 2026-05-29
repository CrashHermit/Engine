from src.core.mechanics.dice import RollTier
from src.core.mechanics.push import improve_magnitude, push_cost


def test_push_cost_table():
    assert push_cost(RollTier.CRIT) == 0
    assert push_cost(RollTier.CLEAN) == 1
    assert push_cost(RollTier.PARTIAL) == 2
    assert push_cost(RollTier.BAD) == 3


def test_improve_magnitude_reduces_and_clamps():
    assert improve_magnitude(3) == 2
    assert improve_magnitude(2, steps=2) == 0
    assert improve_magnitude(0) == 0  # clamps, never negative


def test_improve_magnitude_rejects_negative_steps():
    try:
        improve_magnitude(2, steps=-1)
    except ValueError:
        return
    raise AssertionError("expected ValueError on negative steps")
