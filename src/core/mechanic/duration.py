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

TICK_SECONDS: int = 6

class Unit(StrEnum):
    SIX_SECONDS = "six_seconds"           # 1 tick (A quick reaction / combat round)
    THIRTY_SECONDS = "thirty_seconds"     # 5 ticks (A brief physical exchange)
    ONE_MINUTE = "one_minute"             # 10 ticks (A quick search / lockpick)
    FIVE_MINUTES = "five_minutes"         # 50 ticks (Bandaging, short rest)
    TEN_MINUTES = "ten_minutes"           # 100 ticks (A focused conversation / ritual)
    FIFTEEN_MINUTES = "fifteen_minutes"   # 150 ticks (A quarter-hour / thorough room search)
    THIRTY_MINUTES = "thirty_minutes"     # 300 ticks (A half-hour / short meal)
    ONE_HOUR = "one_hour"                 # 600 ticks (Standard travel / study)
    TWO_HOURS = "two_hours"               # 1200 ticks (Watching a movie / long meeting)
    FOUR_HOURS = "four_hours"             # 2400 ticks (A half workday / guard watch)
    EIGHT_HOURS = "eight_hours"           # 4800 ticks (A full workday / night's sleep)
    TWELVE_HOURS = "twelve_hours"         # 7200 ticks (Half a day / dawn to dusk)
    ONE_DAY = "one_day"                   # 14400 ticks (24 hours)
    THREE_DAYS = "three_days"             # 43200 ticks ("A few days" / weekend trip)
    ONE_WEEK = "one_week"                 # 100800 ticks (7 days)
    TWO_WEEKS = "two_weeks"               # 201600 ticks (A fortnight)
    THREE_WEEKS = "three_weeks"           # 302400 ticks (21 days)
    ONE_MONTH = "one_month"               # 432000 ticks (30 days)
    THREE_MONTHS = "three_months"         # 1296000 ticks (A season / quarter year)
    SIX_MONTHS = "six_months"             # 2592000 ticks (Half a year)
    ONE_YEAR = "one_year"                 # 5256000 ticks (365 days)

TICKS: dict[Unit, int] = {
    Unit.SIX_SECONDS: 1,
    Unit.THIRTY_SECONDS: 5,
    Unit.ONE_MINUTE: 10,
    Unit.FIVE_MINUTES: 50,
    Unit.TEN_MINUTES: 100,
    Unit.FIFTEEN_MINUTES: 150,
    Unit.THIRTY_MINUTES: 300,
    Unit.ONE_HOUR: 600,
    Unit.TWO_HOURS: 1200,
    Unit.FOUR_HOURS: 2400,
    Unit.EIGHT_HOURS: 4800,
    Unit.TWELVE_HOURS: 7200,
    Unit.ONE_DAY: 14400,
    Unit.THREE_DAYS: 43200,
    Unit.ONE_WEEK: 100800,
    Unit.TWO_WEEKS: 201600,
    Unit.THREE_WEEKS: 302400,
    Unit.ONE_MONTH: 432000,
    Unit.THREE_MONTHS: 1296000,
    Unit.SIX_MONTHS: 2592000,
    Unit.ONE_YEAR: 5256000,
}


@dataclass(frozen=True)
class Duration:
    unit: Unit

    @property
    def ticks(self) -> int:
        return TICKS[self.unit]

    @property
    def string(self) -> str:
        return f"{self.unit}"
