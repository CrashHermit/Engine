"""
Persistent harm as a per-part damage pool (decision #19, model "C").

DEFERRED / NOT YET WIRED: this is scaffolding for the player-body-harm system
(§7 of docs/bitd_integration-design.md). It has no callers yet — harm landing
on player parts (`apply_turn_effects`) is unbuilt, and NPCs use per-pillar
clocks (mechanic/effect.py), not this pool. Kept because the feature is fully
specced; wire it when player harm ships.

Each body part carries a small **wound-box pool**; a `harm` threat fills
`magnitude` boxes. The part's `Status` is *derived* from how full the pool is via
tunable thresholds -- so the rest of the engine still reads a clean word
(NORMAL / GRAZED / COMPROMISED / CRITICAL / DESTROYED) while wounds accumulate
underneath.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from src.core.mechanic.magnitude import clamp_magnitude
from src.core.model.part import Status

DEFAULT_CAPACITY: int = 4


@dataclass(frozen=True)
class WoundThresholds:
    grazed: int = 1
    compromised: int = 2
    critical: int = 3
    destroyed: int = 4

    def __post_init__(self) -> None:
        if not 0 < self.grazed <= self.compromised <= self.critical <= self.destroyed:
            raise ValueError(
                "thresholds must be a positive, non-descending ladder "
                f"(grazed={self.grazed}, compromised={self.compromised}, "
                f"critical={self.critical}, destroyed={self.destroyed})"
            )

    def status_for(self, filled: int) -> Status:
        if filled >= self.destroyed:
            return Status.DESTROYED
        if filled >= self.critical:
            return Status.CRITICAL
        if filled >= self.compromised:
            return Status.COMPROMISED
        if filled >= self.grazed:
            return Status.GRAZED
        return Status.NORMAL


@dataclass(frozen=True)
class WoundPool:
    capacity: int = DEFAULT_CAPACITY
    filled: int = 0
    thresholds: WoundThresholds = field(default_factory=WoundThresholds)

    @property
    def status(self) -> Status:
        return self.thresholds.status_for(self.filled)

    @property
    def destroyed(self) -> bool:
        return self.status is Status.DESTROYED


@dataclass(frozen=True)
class WoundApplyResult:
    pool: WoundPool
    overflow: int


def apply_wounds(pool: WoundPool, magnitude: int) -> WoundApplyResult:
    mag: int = clamp_magnitude(magnitude=magnitude)
    total: int = pool.filled + mag
    new_filled: int = min(pool.capacity, total)
    overflow: int = max(0, total - pool.capacity)
    return WoundApplyResult(
        pool=replace(pool, filled=new_filled),
        overflow=overflow,
    )


def heal_wounds(pool: WoundPool, amount: int) -> WoundPool:
    if amount < 0:
        raise ValueError("amount must be non-negative")
    return replace(pool, filled=max(0, pool.filled - amount))
