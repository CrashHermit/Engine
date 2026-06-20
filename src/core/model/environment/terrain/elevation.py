from enum import StrEnum


class ElevationBand(StrEnum):
    SUNKEN = "sunken"
    LOWLAND = "lowland"
    ROLLING = "rolling"
    MIDLAND = "midland"
    HIGHLAND = "highland"
    LOFTY = "lofty"
    SUMMIT = "summit"


ORDER: tuple[ElevationBand, ...] = (
    ElevationBand.SUNKEN,
    ElevationBand.LOWLAND,
    ElevationBand.ROLLING,
    ElevationBand.MIDLAND,
    ElevationBand.HIGHLAND,
    ElevationBand.LOFTY,
    ElevationBand.SUMMIT,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
