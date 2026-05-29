"""Persistent harm as a per-part damage pool (decision #19, model "C").

Each body part carries a small **wound-box pool**; a `harm` threat fills
`magnitude` boxes. The part's `Status` is *derived* from how full the pool is via
tunable thresholds -- so the rest of the engine still reads a clean word
(NORMAL / COMPROMISED / CRITICAL / DESTROYED) while wounds accumulate underneath.

Box count and thresholds are dials (defaults below; tuned at playtest). A
DESTROYED part detaches from the body graph along with everything distal to it --
`distal_parts` computes that set as pure graph traversal; the actual ArcadeDB
mutation lives in a service.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from src.core.mechanics.magnitude import clamp_magnitude
from src.core.model.part import Status

DEFAULT_CAPACITY = 4


@dataclass(frozen=True)
class WoundThresholds:
    """Minimum fill to reach each status (defaults for a 4-box part).

    The defaults are a clean ladder that maps the magnitude scale **1:1** onto the
    status scale for a single hit on a fresh part::

        fill 0 -> NORMAL
        fill 1 -> GRAZED       (Minor)
        fill 2 -> COMPROMISED  (Standard)
        fill 3 -> CRITICAL     (Severe)
        fill 4 -> DESTROYED    (Fatal)

    NORMAL is any fill below ``grazed`` -- it isn't a threshold, it's the floor.
    Wounds still accumulate, so two Minors reach COMPROMISED.
    """

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


@dataclass
class WoundPool:
    capacity: int = DEFAULT_CAPACITY
    filled: int = 0
    thresholds: WoundThresholds = field(default_factory=WoundThresholds)

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ValueError("a wound pool needs at least one box")
        self.filled = max(0, min(self.capacity, self.filled))

    @property
    def status(self) -> Status:
        return self.thresholds.status_for(self.filled)

    @property
    def destroyed(self) -> bool:
        return self.status is Status.DESTROYED

    def apply(self, magnitude: int) -> int:
        """Fill `magnitude` boxes (boxes accumulate).

        Returns the **overflow** beyond capacity (>= 0): a non-zero overflow on a
        vital part is how Fatal harm becomes death (decision #13), decided by the
        caller.
        """
        mag = clamp_magnitude(magnitude)
        total = self.filled + mag
        self.filled = min(self.capacity, total)
        return max(0, total - self.capacity)

    def heal(self, amount: int) -> None:
        """Fiction-gated treatment removes boxes -- granular partial recovery."""
        if amount < 0:
            raise ValueError("cannot heal a negative amount")
        self.filled = max(0, self.filled - amount)


def distal_parts(root: str, attached: Mapping[str, Iterable[str]]) -> set[str]:
    """The root part plus everything distal to it (its descendants).

    `attached` maps a part to the parts attached beyond it, toward the
    extremities (e.g. ``thigh -> [shin]``, ``shin -> [foot]``). Severing a
    DESTROYED part takes the whole limb below it with it.
    """
    seen: set[str] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(attached.get(node, ()))
    return seen
