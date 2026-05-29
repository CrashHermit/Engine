from src.core.mechanics.harm import WoundPool, WoundThresholds, distal_parts
from src.core.model.part import Status


def test_default_status_progression():
    pool = WoundPool()  # capacity 4, thresholds 1/3/4
    assert pool.status is Status.NORMAL

    pool.apply(2)  # Standard
    assert pool.filled == 2
    assert pool.status is Status.COMPROMISED

    pool.apply(1)  # Minor graze tips it
    assert pool.filled == 3
    assert pool.status is Status.CRITICAL

    overflow = pool.apply(2)  # Standard -> caps out, destroyed
    assert pool.filled == 4
    assert pool.status is Status.DESTROYED
    assert pool.destroyed is True
    assert overflow == 1  # the box past capacity (death signal on a vital part)


def test_fatal_fills_exactly_without_overflow():
    pool = WoundPool()
    assert pool.apply(4) == 0
    assert pool.destroyed is True


def test_heal_removes_boxes_and_re_derives_status():
    pool = WoundPool(filled=4)
    assert pool.status is Status.DESTROYED
    pool.heal(1)
    assert pool.filled == 3
    assert pool.status is Status.CRITICAL
    pool.heal(10)  # clamps at zero
    assert pool.filled == 0
    assert pool.status is Status.NORMAL


def test_custom_thresholds_are_tunable():
    # a tougher 6-box part
    pool = WoundPool(capacity=6, thresholds=WoundThresholds(compromised=2, critical=4, destroyed=6))
    pool.apply(2)
    assert pool.status is Status.COMPROMISED
    pool.apply(2)
    assert pool.status is Status.CRITICAL
    pool.apply(2)
    assert pool.status is Status.DESTROYED


def test_apply_clamps_magnitude_input():
    pool = WoundPool(capacity=10)
    pool.apply(99)  # clamped to a max magnitude of 4
    assert pool.filled == 4


def test_invalid_capacity_and_negative_heal():
    try:
        WoundPool(capacity=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on zero capacity")

    try:
        WoundPool().heal(-1)
    except ValueError:
        return
    raise AssertionError("expected ValueError on negative heal")


def test_distal_parts_severs_the_whole_limb():
    attached = {
        "left_thigh": ["left_shin"],
        "left_shin": ["left_foot"],
        "left_foot": [],
        "right_thigh": ["right_shin"],
    }
    assert distal_parts("left_thigh", attached) == {"left_thigh", "left_shin", "left_foot"}
    assert distal_parts("left_foot", attached) == {"left_foot"}
    # an unrelated limb is untouched
    assert "right_thigh" not in distal_parts("left_thigh", attached)


def test_distal_parts_handles_branching_and_cycles():
    attached = {
        "torso": ["left_arm", "right_arm"],
        "left_arm": ["left_hand"],
        "right_arm": [],
        "left_hand": ["torso"],  # pathological cycle must not loop forever
    }
    assert distal_parts("torso", attached) == {
        "torso",
        "left_arm",
        "right_arm",
        "left_hand",
    }
