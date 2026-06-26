"""
Take-highest dice (decision #7).

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

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from random import Random

ATTRIBUTE_CAP: int = 4


class RollTier(StrEnum):
    CRIT = "crit"  # critical success (2+ sixes)
    CLEAN = "clean"  # highest die is a single 6
    PARTIAL = "partial"  # highest die is a 4 or 5
    BAD = "bad"  # highest die is a 1, 2, or 3


@dataclass(frozen=True)
class RollResult:
    dice: tuple[int, ...]
    outcome_die: int
    tier: RollTier
    zero_pool: bool


def _d6(rng: Random) -> int:
    return rng.randint(a=1, b=6)


def classify(dice: Sequence[int], *, zero_pool: bool = False) -> RollTier:
    if not dice:
        raise ValueError("dice must be a non-empty sequence")
    if zero_pool:
        worst: int = min(dice)
        if worst == 6:
            return RollTier.CLEAN
        if worst >= 4:
            return RollTier.PARTIAL
        return RollTier.BAD

    if dice.count(6) >= 2:
        return RollTier.CRIT
    best: int = max(dice)
    if best == 6:
        return RollTier.CLEAN
    if best >= 4:
        return RollTier.PARTIAL
    return RollTier.BAD


def result_from_dice(dice: Sequence[int], *, zero_pool: bool = False) -> RollResult:
    if not dice:
        raise ValueError("dice must be a non-empty sequence")
    rolled: tuple[int, ...] = tuple(dice)
    outcome_die: int = min(rolled) if zero_pool else max(rolled)
    return RollResult(
        dice=rolled,
        outcome_die=outcome_die,
        tier=classify(dice=rolled, zero_pool=zero_pool),
        zero_pool=zero_pool,
    )


def roll_pool(pool: int, *, rng: Random | None = None) -> RollResult:
    rng_value: Random = rng or Random()
    if pool <= 0:
        dice: tuple[int, ...] = (_d6(rng_value), _d6(rng_value))
        return result_from_dice(dice, zero_pool=True)
    dice: tuple[int, ...] = tuple(_d6(rng_value) for _ in range(pool))
    return result_from_dice(dice, zero_pool=False)
