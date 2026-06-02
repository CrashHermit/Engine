"""
Effect-on-target (the mirror of threat-on-player).

One action roll drives two axes. Threats coming *back* at the player are scaled
in scaling.py; the effect the player lands *on* a target is scaled here. An
entity carries a single clock (a WoundPool sized by its danger); the player's
effect fills it, and the entity is defeated when it is full.

Effect is the action tier shifted one step by potency — the rolled attribute
pool against the target's danger — so a rat and a dragon don't take the same hit
from the same roll. A miss (BAD tier) lands nothing regardless of potency.
"""

from src.core.mechanic.dice import RollTier
from src.core.mechanic.harm import WoundPool
from src.core.model.entity import Danger
from src.core.model.resolution import Effect

CAPACITY_BY_DANGER: dict[Danger, int] = {
    Danger.LOW: 4,
    Danger.STANDARD: 6,
    Danger.ELITE: 8,
    Danger.DEADLY: 10,
}

_TIER_EFFECT: dict[RollTier, Effect | None] = {
    RollTier.CRIT: Effect.GREAT,
    RollTier.CLEAN: Effect.STANDARD,
    RollTier.PARTIAL: Effect.LIMITED,
    RollTier.BAD: None,
}

_DANGER_RANK: dict[Danger, int] = {
    Danger.LOW: 1,
    Danger.STANDARD: 2,
    Danger.ELITE: 3,
    Danger.DEADLY: 4,
}

# Ordinal ladder for the one-step potency shift; index 0 is "no effect".
_EFFECT_LADDER: tuple[Effect | None, ...] = (None, Effect.LIMITED, Effect.STANDARD, Effect.GREAT)
_EFFECT_SEGMENTS: dict[Effect | None, int] = {None: 0, Effect.LIMITED: 1, Effect.STANDARD: 2, Effect.GREAT: 3}


def capacity_for_danger(danger: Danger) -> int:
    return CAPACITY_BY_DANGER[danger]


def new_clock_for(danger: Danger) -> WoundPool:
    return WoundPool(capacity=capacity_for_danger(danger), filled=0)


def effect_from_tier(tier: RollTier) -> Effect | None:
    return _TIER_EFFECT[tier]


def potency_shift(effect: Effect | None, pool: int, danger: Danger | None) -> Effect | None:
    """Shift the effect one step by potency. A miss stays a miss."""
    if effect is None:
        return None
    rank = _DANGER_RANK[danger] if danger is not None else 2
    idx = _EFFECT_LADDER.index(effect)
    if pool - rank >= 2:
        idx += 1
    elif rank - pool >= 2:
        idx -= 1
    idx = max(0, min(len(_EFFECT_LADDER) - 1, idx))
    return _EFFECT_LADDER[idx]


def effect_segments(effect: Effect | None) -> int:
    return _EFFECT_SEGMENTS[effect]


def is_defeated(clock: WoundPool) -> bool:
    """An entity is defeated when its clock is full. (Distinct from WoundPool's
    body-part Status ladder, which is meaningless for an abstract NPC clock.)"""
    return clock.filled >= clock.capacity
