from enum import StrEnum


class CloudCoverBand(StrEnum):
    CLEAR = "clear"
    FEW = "few"
    SCATTERED = "scattered"
    BROKEN = "broken"
    MOSTLY = "mostly"
    OVERCAST = "overcast"
    LEADEN = "leaden"


ORDER: tuple[CloudCoverBand, ...] = (
    CloudCoverBand.CLEAR,
    CloudCoverBand.FEW,
    CloudCoverBand.SCATTERED,
    CloudCoverBand.BROKEN,
    CloudCoverBand.MOSTLY,
    CloudCoverBand.OVERCAST,
    CloudCoverBand.LEADEN,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
