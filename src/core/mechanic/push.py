"""
Unified push / resist (decision #11).

Pre-roll push is gone. *After* a roll, the player may spend stress to bump the
outcome one step (reduce a consequence one magnitude) or gain more effect. The
improvement always lands; the dice only set the **price** -- a flat cost keyed to
the highest die of the push roll:

    crit -> 0 stress
    6    -> 1
    4-5  -> 2
    1-3  -> 3
"""

from __future__ import annotations

from src.core.mechanic.dice import RollTier
from src.core.mechanic.magnitude import clamp_magnitude

# Push for effect (action-level): spend a flat stress cost to land one extra
# effect segment on the target's pillar clock. Blades-standard flat 2.
PUSH_FOR_EFFECT_STRESS: int = 2
PUSH_FOR_EFFECT_SEGMENTS: int = 1

PUSH_COST: dict[RollTier, int] = {
    RollTier.CRIT: 0,
    RollTier.CLEAN: 1,
    RollTier.PARTIAL: 2,
    RollTier.BAD: 3,
}


def push_cost(tier: RollTier) -> int:
    return PUSH_COST[tier]


def improve_magnitude(landed_magnitude: int, steps: int = 1) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    return clamp_magnitude(magnitude=landed_magnitude - steps)
