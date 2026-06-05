"""
Discrete game time (1 tick = 6 seconds).

All deterministic time in the engine is counted in integer **ticks**. Fictional
durations are expressed as a `Span` — a `(unit, count)` pair drawn from a fixed
ladder — which converts to an exact tick total. The ladder is geometric, so
relative precision stays roughly constant across six orders of magnitude
(seconds to years).

The `count` is **scale-gated**, and that gate is the whole point:

  * Fine units (Round … Night): `count` is always 1. You pick the rung. A count
    here would demand sub-bucket precision the fiction never contains — the
    "43 seconds" trap.
  * Coarse units (Day, Week, Month, Year): `count` is 1–`MAX_COUNT`. This is
    where a GM-determined long span lives ("about 3 weeks", "5 months"): a small
    integer at coarse *relative* precision, which is a real judgement, not
    fabricated precision. The counts also fill the wide geometric gaps between
    the four coarse units, so the long tail needs no extra rungs.

`normalize`/`span_from_ticks` canonicalise any tick total back onto the ladder,
applying the step-up rule: keep the smallest coarse unit whose count fits the
cap (preserving resolution), stepping up only when the count would overflow.

This module is pure: no randomness, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import log

TICK_SECONDS: int = 6
MAX_COUNT: int = 9  # count cap on coarse units before a step-up


class Unit(StrEnum):
    ROUND = "round"
    MOMENT = "moment"
    MINUTE = "minute"
    SPELL = "spell"
    STRETCH = "stretch"
    HOUR = "hour"
    WATCH = "watch"
    NIGHT = "night"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


# Ladder in ascending tick order. Every value is an exact 6s conversion of its
# fictional span (90s -> 15, 5min -> 50, 24h -> 14400, ...), so the names carry
# no fabricated precision.
TICKS: dict[Unit, int] = {
    Unit.ROUND: 1,  # 6 s
    Unit.MOMENT: 5,  # ~30 s
    Unit.MINUTE: 15,  # ~90 s
    Unit.SPELL: 50,  # ~5 min
    Unit.STRETCH: 150,  # ~15 min
    Unit.HOUR: 600,  # 1 h
    Unit.WATCH: 2_400,  # ~4 h
    Unit.NIGHT: 4_800,  # ~8 h
    Unit.DAY: 14_400,  # 24 h
    Unit.WEEK: 100_800,  # 7 d
    Unit.MONTH: 432_000,  # ~30 d
    Unit.YEAR: 5_256_000,  # 365 d
}

# Units that may carry a count > 1. Everything below is single-pick (count 1).
COARSE: frozenset[Unit] = frozenset({Unit.DAY, Unit.WEEK, Unit.MONTH, Unit.YEAR})

# Cached ascending views used by the canonicaliser.
_ASCENDING: tuple[Unit, ...] = tuple(sorted(TICKS, key=TICKS.__getitem__))
_COARSE_ASCENDING: tuple[Unit, ...] = tuple(u for u in _ASCENDING if u in COARSE)
_FINE: tuple[Unit, ...] = tuple(u for u in _ASCENDING if u not in COARSE)


@dataclass(frozen=True)
class Span:
    """A fictional duration as `count` of `unit`. Validated to the scale gate.

    Fine units must have count 1; coarse units allow 1..MAX_COUNT.
    """

    unit: Unit
    count: int = 1

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError(f"count must be >= 1, got {self.count}")
        if self.unit not in COARSE and self.count != 1:
            raise ValueError(
                f"fine unit {self.unit} must have count 1, got {self.count}"
            )
        if self.count > MAX_COUNT:
            raise ValueError(f"count must be <= {MAX_COUNT}, got {self.count}")

    @property
    def ticks(self) -> int:
        return self.count * TICKS[self.unit]


def span_from_ticks(ticks: int) -> Span:
    """Project a tick total onto the canonical ladder position.

    Coarse range: the *smallest* coarse unit whose rounded count fits the cap —
    smallest-first preserves resolution (3 weeks stays Week x3 rather than
    collapsing to Month x1), and we step up only when the count would overflow.
    Fine range: the nearest rung in log space (honest for a geometric ladder),
    always at count 1.
    """
    ticks = max(1, round(ticks))

    if round(ticks / TICKS[Unit.DAY]) >= 1:
        for unit in _COARSE_ASCENDING:
            count = round(ticks / TICKS[unit])
            if 1 <= count <= MAX_COUNT:
                return Span(unit, count)
        return Span(Unit.YEAR, MAX_COUNT)  # ceiling: clamp the largest unit

    nearest = min(_FINE, key=lambda u: abs(log(ticks) - log(TICKS[u])))
    return Span(nearest, 1)


def normalize(unit: Unit, count: int) -> Span:
    """Lenient factory: accept any `(unit, count)` and return the canonical Span.

    Accepts a fine unit given a count, or a coarse count past the cap —
    applies the step-up rule to reach the same tick total.
    """
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count}")
    return span_from_ticks(count * TICKS[unit])
