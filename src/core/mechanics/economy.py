"""The survival economy: stress, trauma, permadeath, vice relief (#11-14).

Stress rises (push/resist, consequences) and falls (vice relief only). When a
stress gain would overflow the track, the character takes a trauma and stress
resets to 0; at the trauma cap the character is **lost** (decision #13). Relief
is vice-only: indulging clears stress equal to the vice roll, and overshooting
your current stress means you **overindulge** (decision #12).

All pure functions over plain values -- the orchestration (rolling, persisting)
lives in the graph/services.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_STRESS_MAX = 9
DEFAULT_TRAUMA_MAX = 4


@dataclass(frozen=True)
class EconomyConfig:
    stress_max: int = DEFAULT_STRESS_MAX
    trauma_max: int = DEFAULT_TRAUMA_MAX


@dataclass(frozen=True)
class StressResult:
    stress: int
    trauma: int
    trauma_gained: bool
    lost: bool  # reached the trauma cap -- character is retired/dead/broken


@dataclass(frozen=True)
class ViceResult:
    stress: int
    cleared: int
    overindulged: bool


def add_stress(
    stress: int,
    trauma: int,
    amount: int,
    *,
    config: EconomyConfig = EconomyConfig(),
) -> StressResult:
    """Add stress; overflow trades the excess for one trauma and resets to 0.

    A single call yields at most one trauma (callers add stress in discrete
    events); the remainder past the track is discarded, as in Blades.
    """
    if amount < 0:
        raise ValueError("use vice_clear to reduce stress, not a negative add")

    total = stress + amount
    if total <= config.stress_max:
        return StressResult(total, trauma, trauma_gained=False, lost=False)

    new_trauma = trauma + 1
    return StressResult(
        stress=0,
        trauma=new_trauma,
        trauma_gained=True,
        lost=new_trauma >= config.trauma_max,
    )


def vice_clear(stress: int, vice_roll: int) -> ViceResult:
    """Indulge a vice: clear `vice_roll` stress (the vice roll's outcome die).

    Overindulge when the roll **exceeds** current stress -- the anti-spam gate
    that makes relief safe when strung-out and risky when nearly fresh (#12).
    """
    if vice_roll < 0:
        raise ValueError("a vice roll cannot be negative")
    cleared = min(stress, vice_roll)
    return ViceResult(
        stress=stress - cleared,
        cleared=cleared,
        overindulged=vice_roll > stress,
    )
