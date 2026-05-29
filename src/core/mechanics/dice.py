"""Take-highest dice (decision #7).

Pool = the attribute's 0-4 rating (decision #8/#20). Roll that many d6 and take
the highest; a pool of 0 rolls **2d6 and takes the worst** (and cannot crit).
The highest die maps to a result tier:

    crit (2+ sixes) -> avoided + a benefit
    6               -> avoided
    4-5             -> reduced
    1-3             -> full

This module is pure: `roll_pool` injects randomness via an optional `rng`, and
`classify` / `result_from_dice` let callers (and tests) reason about fixed dice
with no randomness at all.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

#: The 0-4 attribute rating cap (decisions #8, #20).
ATTRIBUTE_CAP = 4


class RollTier(StrEnum):
    CRIT = "crit"        # two or more sixes
    CLEAN = "clean"      # highest die is a single 6
    PARTIAL = "partial"  # highest die is 4 or 5
    BAD = "bad"          # highest die is 1-3


@dataclass(frozen=True)
class RollResult:
    dice: tuple[int, ...]  # every die rolled
    outcome_die: int       # the die that decides the tier (max; for a 0-pool, the worst)
    tier: RollTier
    zero_pool: bool        # True when rolled under the 0-rating "2d6 take worst" rule


def _d6(rng: random.Random) -> int:
    return rng.randint(1, 6)


def classify(dice: Sequence[int], *, zero_pool: bool = False) -> RollTier:
    """Map a set of dice to its result tier.

    A `zero_pool` roll takes the *worst* die and can never crit.
    """
    if not dice:
        raise ValueError("cannot classify an empty roll")

    if zero_pool:
        worst = min(dice)
        if worst == 6:
            return RollTier.CLEAN
        if worst >= 4:
            return RollTier.PARTIAL
        return RollTier.BAD

    if sum(1 for d in dice if d == 6) >= 2:
        return RollTier.CRIT
    highest = max(dice)
    if highest == 6:
        return RollTier.CLEAN
    if highest >= 4:
        return RollTier.PARTIAL
    return RollTier.BAD


def result_from_dice(dice: Sequence[int], *, zero_pool: bool = False) -> RollResult:
    """Build a `RollResult` from already-known dice (no randomness)."""
    tier = classify(dice, zero_pool=zero_pool)
    outcome_die = min(dice) if zero_pool else max(dice)
    return RollResult(tuple(dice), outcome_die, tier, zero_pool)


def roll_pool(pool: int, *, rng: random.Random | None = None) -> RollResult:
    """Roll a dice pool. `pool <= 0` triggers the 2d6-take-worst rule."""
    rng = rng or random
    if pool <= 0:
        dice = (_d6(rng), _d6(rng))
        return result_from_dice(dice, zero_pool=True)
    dice = tuple(_d6(rng) for _ in range(pool))
    return result_from_dice(dice, zero_pool=False)
