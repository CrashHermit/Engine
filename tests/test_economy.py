from src.core.mechanics.economy import (
    EconomyConfig,
    add_stress,
    vice_clear,
)


def test_add_stress_below_track():
    res = add_stress(stress=3, trauma=0, amount=2)
    assert res.stress == 5
    assert res.trauma == 0
    assert res.trauma_gained is False
    assert res.lost is False


def test_add_stress_exactly_full_does_not_overflow():
    res = add_stress(stress=7, trauma=1, amount=2)  # 9 == default max
    assert res.stress == 9
    assert res.trauma_gained is False


def test_overflow_takes_one_trauma_and_resets():
    res = add_stress(stress=8, trauma=1, amount=2)  # 10 > 9
    assert res.stress == 0
    assert res.trauma == 2
    assert res.trauma_gained is True
    assert res.lost is False


def test_reaching_trauma_cap_is_lost():
    res = add_stress(stress=9, trauma=3, amount=1)
    assert res.trauma == 4
    assert res.lost is True


def test_custom_economy_config():
    cfg = EconomyConfig(stress_max=4, trauma_max=2)
    res = add_stress(stress=4, trauma=1, amount=1, config=cfg)
    assert res.stress == 0
    assert res.trauma == 2
    assert res.lost is True


def test_add_stress_rejects_negative():
    try:
        add_stress(stress=3, trauma=0, amount=-1)
    except ValueError:
        return
    raise AssertionError("expected ValueError on negative stress add")


def test_vice_clear_partial():
    res = vice_clear(stress=5, vice_roll=4)
    assert res.cleared == 4
    assert res.stress == 1
    assert res.overindulged is False


def test_vice_clear_overindulge_when_roll_exceeds_stress():
    res = vice_clear(stress=2, vice_roll=5)
    assert res.cleared == 2  # can't clear more than you have
    assert res.stress == 0
    assert res.overindulged is True


def test_vice_clear_on_fresh_character_overindulges():
    res = vice_clear(stress=0, vice_roll=1)
    assert res.cleared == 0
    assert res.overindulged is True  # 1 > 0


def test_vice_clear_rejects_negative_roll():
    try:
        vice_clear(stress=3, vice_roll=-1)
    except ValueError:
        return
    raise AssertionError("expected ValueError on negative vice roll")
