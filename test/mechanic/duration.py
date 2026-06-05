from __future__ import annotations

import pytest

from src.core.mechanic.duration import (
    COARSE,
    MAX_COUNT,
    TICKS,
    Duration,
    Unit,
    normalize,
    span_from_ticks,
)


def test_ladder_is_strictly_ascending():
    values = [TICKS[u] for u in Unit]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


@pytest.mark.parametrize(
    "unit,expected",
    [
        (Unit.ROUND, 1),
        (Unit.MINUTE, 15),
        (Unit.HOUR, 600),
        (Unit.DAY, 14_400),
        (Unit.WEEK, 100_800),
        (Unit.YEAR, 5_256_000),
    ],
)
def test_known_tick_values(unit, expected):
    assert TICKS[unit] == expected
    # Every rung is an exact 6s conversion (a whole number of ticks).
    assert TICKS[unit] == Duration(unit).ticks


def test_coarse_span_ticks_multiply_by_count():
    assert Duration(Unit.WEEK, 3).ticks == 3 * 100_800
    assert Duration(Unit.MONTH, 5).ticks == 5 * 432_000


# ── the scale gate ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("unit", [u for u in Unit if u not in COARSE])
def test_fine_unit_rejects_count_above_one(unit):
    with pytest.raises(ValueError):
        Duration(unit, 2)


@pytest.mark.parametrize("unit", sorted(COARSE))
def test_coarse_unit_allows_counts_up_to_cap(unit):
    assert Duration(unit, MAX_COUNT).ticks == MAX_COUNT * TICKS[unit]
    with pytest.raises(ValueError):
        Duration(unit, MAX_COUNT + 1)


def test_count_must_be_positive():
    with pytest.raises(ValueError):
        Duration(Unit.DAY, 0)


# ── canonicalisation + step-up ──────────────────────────────────────────────


def test_three_weeks_keeps_resolution():
    # Smallest-first: 3 weeks stays Week x3, not collapsed to ~Month x1.
    assert span_from_ticks(Duration(Unit.WEEK, 3).ticks) == Duration(Unit.WEEK, 3)


def test_overflowing_count_steps_up_a_unit():
    # 10 weeks overflows the Week cap -> rolls up to ~2 months.
    assert normalize(Unit.WEEK, 10) == Duration(Unit.MONTH, 2)


def test_five_months_round_trips():
    assert normalize(Unit.MONTH, 5) == Duration(Unit.MONTH, 5)


def test_few_days_stay_in_days():
    assert span_from_ticks(Duration(Unit.DAY, 4).ticks) == Duration(Unit.DAY, 4)


def test_fine_unit_with_a_count_projects_to_a_rung():
    # A fine unit should never carry a count; normalize re-projects it.
    result = normalize(Unit.HOUR, 5)  # 3000 ticks, between Watch and Night
    assert result.count == 1
    assert result.unit not in COARSE


@pytest.mark.parametrize(
    "unit",
    [Unit.ROUND, Unit.MINUTE, Unit.HOUR, Unit.NIGHT],
)
def test_exact_fine_rung_round_trips(unit):
    assert span_from_ticks(TICKS[unit]) == Duration(unit, 1)


def test_huge_total_clamps_at_year_ceiling():
    assert span_from_ticks(10**12) == Duration(Unit.YEAR, MAX_COUNT)


def test_sub_round_floors_to_round():
    assert span_from_ticks(0) == Duration(Unit.ROUND, 1)
