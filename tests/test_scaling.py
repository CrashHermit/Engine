from src.core.mechanics.dice import RollTier
from src.core.mechanics.scaling import Position, scale_threat


def test_six_and_crit_avoid():
    clean = scale_threat(3, RollTier.CLEAN)
    assert clean.landed_magnitude == 0
    assert clean.avoided is True
    assert clean.crit is False

    crit = scale_threat(4, RollTier.CRIT)
    assert crit.landed_magnitude == 0
    assert crit.avoided is True
    assert crit.crit is True


def test_risky_default():
    # 4-5 reduces by one; 1-3 lands full
    assert scale_threat(2, RollTier.PARTIAL).landed_magnitude == 1
    assert scale_threat(2, RollTier.BAD).landed_magnitude == 2


def test_desperate_hardens():
    # only a 6 avoids; 4-5 now lands full
    assert scale_threat(2, RollTier.PARTIAL, Position.DESPERATE).landed_magnitude == 2
    assert scale_threat(3, RollTier.BAD, Position.DESPERATE).landed_magnitude == 3


def test_controlled_softens():
    assert scale_threat(3, RollTier.PARTIAL, Position.CONTROLLED).landed_magnitude == 1
    assert scale_threat(3, RollTier.BAD, Position.CONTROLLED).landed_magnitude == 2


def test_reduction_clamps_at_zero_without_marking_avoided():
    out = scale_threat(1, RollTier.PARTIAL)  # 1 - 1 = 0
    assert out.landed_magnitude == 0
    assert out.avoided is False  # avoided is reserved for 6 / crit


def test_zero_base_stays_zero():
    assert scale_threat(0, RollTier.BAD, Position.DESPERATE).landed_magnitude == 0
