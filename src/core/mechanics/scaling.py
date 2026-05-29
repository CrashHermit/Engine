"""Outcome -> threat scaling (decisions #7, #15-17).

The threat's base magnitude is fixed *before* the roll by the classifiers; this
module is the deterministic code that scales it by the roll tier and position.

    crit / 6  -> avoided (magnitude 0); crit also owes a benefit
    4-5       -> reduced
    1-3       -> full

`position` (decision #16) bends the 4-5 / 1-3 rungs: **risky** is the default,
**desperate** makes 4-5 land full (only a 6 avoids), **controlled** softens both.
Push/resist (see `push`) can reduce the landed magnitude one step further.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.mechanics.dice import RollTier
from src.core.mechanics.magnitude import clamp_magnitude


class Position(StrEnum):
    CONTROLLED = "controlled"
    RISKY = "risky"
    DESPERATE = "desperate"


# Magnitude *reduction* applied on the non-avoiding tiers, per position.
# crit / clean always avoid outright, so they aren't in the table.
_REDUCTION: dict[Position, dict[RollTier, int]] = {
    Position.CONTROLLED: {RollTier.PARTIAL: 2, RollTier.BAD: 1},
    Position.RISKY: {RollTier.PARTIAL: 1, RollTier.BAD: 0},
    Position.DESPERATE: {RollTier.PARTIAL: 0, RollTier.BAD: 0},
}


@dataclass(frozen=True)
class Outcome:
    landed_magnitude: int  # what actually lands, 0-4
    avoided: bool          # the roll cleanly neutralised the threat (6 / crit)
    crit: bool             # a benefit is owed on top


def scale_threat(
    base_magnitude: int,
    tier: RollTier,
    position: Position = Position.RISKY,
) -> Outcome:
    """Scale a pre-rolled base magnitude by the roll tier and position."""
    base = clamp_magnitude(base_magnitude)

    if tier in (RollTier.CRIT, RollTier.CLEAN):
        return Outcome(landed_magnitude=0, avoided=True, crit=tier is RollTier.CRIT)

    reduction = _REDUCTION[position][tier]
    return Outcome(
        landed_magnitude=clamp_magnitude(base - reduction),
        avoided=False,
        crit=False,
    )
