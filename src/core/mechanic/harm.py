"""
Persistent harm as a per-part damage pool (decision #19, model "C").

Each body part carries a small **wound-box pool**; a `harm` threat fills
`magnitude` boxes. The part's `Status` is *derived* from how full the pool is via
tunable thresholds -- so the rest of the engine still reads a clean word
(NORMAL / GRAZED / COMPROMISED / CRITICAL / DESTROYED) while wounds accumulate
underneath.
"""

from dataclasses import dataclass, field
from core.mechanic.magnitude import clamp_magnitude
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

    def apply(self, magnitude: int) -> None:
        mag: int = clamp_magnitude(magnitude=magnitude)
        total: int = self.filled + mag
        self.filled = min(self.capacity, total)
        return max(0, total - self.capacity)

    def heal(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.filled = max(0, self.filled - amount)
