from enum import StrEnum


class AlignmentBand(StrEnum):
    EVIL = "evil"
    NEUTRAL = "neutral"
    GOOD = "good"


ORDER: tuple[AlignmentBand, ...] = (
    AlignmentBand.EVIL,
    AlignmentBand.NEUTRAL,
    AlignmentBand.GOOD,
)

BREAKPOINTS: tuple[float, ...] = (1 / 3, 2 / 3)
