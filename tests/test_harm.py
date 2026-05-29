from src.core.mechanics.harm import WoundPool, WoundThresholds, distal_parts
from src.core.model.part import Status


def test_default_status_ladder_is_consecutive():
    # No skipped fill level, and NORMAL is a real band (0-1), not a single point.
    pool = WoundPool()  # capacity 4, thresholds 2/3/4
    expected = [
        Status.NORMAL,       # 0
        Status.NORMAL,       # 1 — a Minor scratch
        Status.COMPROMISED,  # 2
        Status.CRITICAL,     # 3
        Status.DESTROYED,    # 4
    ]
    for fill, status in enumerate(expected):
        assert WoundPool(filled=fill).status is status


def test_default_status_progression():
    pool = WoundPool()  # capacity 4, thresholds 2/3/4
    assert pool.status is Status.NORMAL

    pool.apply(1)  # Minor — still just a scratch
    assert pool.filled == 1
    assert pool.status is Status.NORMAL

    pool.apply(1)  # a second Minor accumulates
    assert pool.filled == 2
    assert pool.status is Status.COMPROMISED

    pool.apply(1)
    assert pool.filled == 3
    assert pool.status is Status.CRITICAL

    overflow = pool.apply(2)  # caps out, destroyed
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


def test_invalid_thresholds_rejected():
    for bad in (
        {"compromised": 0},                            # must be positive
        {"compromised": 3, "critical": 2},             # must not descend
        {"compromised": 2, "critical": 5, "destroyed": 4},
    ):
        try:
            WoundThresholds(**bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad}")


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
