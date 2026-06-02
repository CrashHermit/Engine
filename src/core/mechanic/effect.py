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
from src.core.model.entity import Danger, ThreatPillar
from src.core.model.resolution import Effect

# Clock capacity by danger. Tuned so weak foes are taken out in a single solid
# exchange (Blades: a lone guard just goes down) while dangerous foes become a
# real multi-exchange clock. Effect lands 1-3 segments, so LOW one-shots on any
# hit, STANDARD takes ~two, and DEADLY is a genuine struggle.
CAPACITY_BY_DANGER: dict[Danger, int] = {
    Danger.LOW: 1,
    Danger.STANDARD: 3,
    Danger.ELITE: 6,
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


def pillar_capacity(
    danger: Danger,
    pillar: ThreatPillar,
    profile: dict[ThreatPillar, int] | None = None,
) -> int:
    """Clock size for breaking a given pillar.

    No profile (unauthored creature) -> uniform from danger (every condition
    equally hard for the tier). An authored profile is authoritative: a listed
    pillar uses its capacity; a pillar the profile omits is IMMUNE (capacity 0
    -> can't be broken that way), which is how a golem resists WILLING or a
    mindless thing resists AWARE."""
    if profile:
        return profile.get(pillar, 0)
    return capacity_for_danger(danger)


# How the narrator should frame a broken pillar — kept structural so prose can't
# silently turn a rout into a kill.
_PILLAR_OUTCOME: dict[ThreatPillar, str] = {
    ThreatPillar.EXISTS: "is destroyed — frame this as a kill/end, not a mere wound",
    ThreatPillar.CAPABLE: "is disabled (disarmed, crippled, restrained) and can no longer act against you",
    ThreatPillar.AWARE: "loses track of you — frame this as slipping out of its awareness, it is unharmed",
    ThreatPillar.IN_REACH: "can no longer reach you — frame this as breaking away / being cut off, it is unharmed",
    ThreatPillar.WILLING: "loses its nerve — frame this as backing down, fleeing, or surrendering, NOT dying",
}


def outcome_clause(pillar: ThreatPillar, name: str) -> str:
    return f"The {name} {_PILLAR_OUTCOME[pillar]}."


# Default condition under which a broken pillar reverts and the foe re-engages.
# EXISTS is permanent (the creature is gone), so it has no return.
_PILLAR_RETURNS_WHEN: dict[ThreatPillar, str] = {
    ThreatPillar.CAPABLE: "it recovers, is freed, or finds another means to act",
    ThreatPillar.AWARE: "you make noise, move into its view, or it searches and finds you",
    ThreatPillar.IN_REACH: "you re-enter its space, it pursues you, or you are cornered",
    ThreatPillar.WILLING: "you show weakness, it is cornered with no escape, or reinforcements embolden it",
}


def returns_when_for(pillar: ThreatPillar) -> str:
    return _PILLAR_RETURNS_WHEN.get(pillar, "")
