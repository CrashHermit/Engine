from __future__ import annotations

import pytest

from src.core.mechanic.duration import TICKS, Duration, Unit


def test_ladder_is_strictly_ascending():
    values = [TICKS[u] for u in Unit]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


@pytest.mark.parametrize(
    "unit,expected",
    [
        (Unit.SIX_SECONDS, 1),
        (Unit.ONE_MINUTE, 10),
        (Unit.ONE_HOUR, 600),
        (Unit.ONE_DAY, 14_400),
        (Unit.ONE_WEEK, 100_800),
        (Unit.ONE_YEAR, 5_256_000),
    ],
)
def test_known_tick_values(unit, expected):
    assert TICKS[unit] == expected


@pytest.mark.parametrize("unit", list(Unit))
def test_duration_ticks_matches_table(unit):
    assert Duration(unit).ticks == TICKS[unit]


def test_duration_is_immutable():
    d = Duration(Unit.ONE_HOUR)
    with pytest.raises((AttributeError, TypeError)):
        d.unit = Unit.ONE_DAY  # type: ignore[misc]
