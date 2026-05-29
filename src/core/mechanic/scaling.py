from enum import StrEnum
from dataclasses import dataclass
from core.mechanic.magnitude import clamp_magnitude
from src.core.mechanic.dice import RollTier

class Position(StrEnum):
    CONTROLLED = "controlled"
    RISKY = "risky"
    DESPERATE = "desperate"

REDUCTION: dict[Position, dict[RollTier, int]] = {
    Position.CONTROLLED: {
        RollTier.PARTIAL: 2,
        RollTier.BAD: 1,
    },
    Position.RISKY: {
        RollTier.PARTIAL: 1,
        RollTier.BAD: 0,
    },
    Position.DESPERATE: {
        RollTier.PARTIAL: 0,
        RollTier.BAD: 0,
    },
}


@dataclass(frozen=True)
class Outcome:
    landed_magnitude: int
    avoided: bool
    crit: bool

def scale_threat(
    base_magnitude: int,
    tier: RollTier,
    position: Position = Position.RISKY,
) -> Outcome:
    base: int = clamp_magnitude(magnitude=base_magnitude)

    if tier == RollTier.CLEAN:
        return Outcome(
            landed_magnitude=0,
            avoided=True,
            crit=False,
        )
    if tier == RollTier.CRIT:
        return Outcome(
            landed_magnitude=0,
            avoided=True,
            crit=True,
        )

    reduction: int = REDUCTION[position][tier]

    landed_magnitude: int = clamp_magnitude(magnitude=base - reduction)

    return Outcome(
        landed_magnitude=landed_magnitude,
        avoided=False,
        crit=False,
    )