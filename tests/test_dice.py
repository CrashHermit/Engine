import random

from src.core.mechanics.dice import (
    RollTier,
    classify,
    result_from_dice,
    roll_pool,
)


def test_classify_normal_pool():
    assert classify([6, 6]) is RollTier.CRIT
    assert classify([6, 6, 1]) is RollTier.CRIT
    assert classify([6, 2]) is RollTier.CLEAN
    assert classify([6]) is RollTier.CLEAN
    assert classify([5, 1]) is RollTier.PARTIAL
    assert classify([4]) is RollTier.PARTIAL
    assert classify([3, 3, 2]) is RollTier.BAD
    assert classify([1]) is RollTier.BAD


def test_classify_zero_pool_takes_worst_and_never_crits():
    assert classify([6, 6], zero_pool=True) is RollTier.CLEAN  # worst is 6
    assert classify([6, 5], zero_pool=True) is RollTier.PARTIAL  # worst is 5
    assert classify([6, 3], zero_pool=True) is RollTier.BAD  # worst is 3
    assert classify([4, 1], zero_pool=True) is RollTier.BAD


def test_classify_empty_raises():
    try:
        classify([])
    except ValueError:
        return
    raise AssertionError("expected ValueError on empty roll")


def test_result_from_dice_outcome_die():
    assert result_from_dice([2, 5, 3]).outcome_die == 5
    zero = result_from_dice([6, 2], zero_pool=True)
    assert zero.outcome_die == 2
    assert zero.zero_pool is True


def test_roll_pool_size_and_zero_rule():
    rng = random.Random(1234)
    res = roll_pool(3, rng=rng)
    assert len(res.dice) == 3
    assert res.zero_pool is False
    assert all(1 <= d <= 6 for d in res.dice)

    zero = roll_pool(0, rng=random.Random(1))
    assert len(zero.dice) == 2
    assert zero.zero_pool is True
    # negative pool is also treated as the 0-rating rule
    assert roll_pool(-1, rng=random.Random(1)).zero_pool is True


def test_roll_pool_is_deterministic_under_seed():
    a = roll_pool(2, rng=random.Random(42))
    b = roll_pool(2, rng=random.Random(42))
    assert a == b
