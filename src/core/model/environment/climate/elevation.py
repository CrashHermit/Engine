from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ElevationBand(StrEnum):
    SUNKEN = "sunken"
    LOWLAND = "lowland"
    ROLLING = "rolling"
    MIDLAND = "midland"
    HIGHLAND = "highland"
    LOFTY = "lofty"
    SUMMIT = "summit"


@dataclass(frozen=True)
class ElevationBandInfo:
    label: str
    description: str
    flavor: list[str]


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

INFO: dict[ElevationBand, ElevationBandInfo] = {
    ElevationBand.SUNKEN: ElevationBandInfo(
        label="Sunken",
        description="Below the surrounding grade — hollows, basins, and depressions.",
        flavor=[
            "Air pools cold and still.",
            "Fog lingers longer here.",
            "Sound muffles against slopes.",
            "Water collects without asking.",
            "The sky feels farther away.",
        ],
    ),
    ElevationBand.LOWLAND: ElevationBandInfo(
        label="Lowland",
        description="Flat low country — rivers, coasts, and open plains.",
        flavor=[
            "Horizons run wide.",
            "Winds cross unbroken.",
            "Floods leave their mark.",
            "Travel is fast when dry.",
            "Settlements favor these reaches.",
        ],
    ),
    ElevationBand.ROLLING: ElevationBandInfo(
        label="Rolling",
        description="Gentle rises and falls that hide and reveal.",
        flavor=[
            "Valleys break sightlines.",
            "Creeks thread the folds.",
            "Rain pools in dips.",
            "Paths crest and dip endlessly.",
            "Shelter is one hill away.",
        ],
    ),
    ElevationBand.MIDLAND: ElevationBandInfo(
        label="Midland",
        description="Moderate highlands between plain and peak.",
        flavor=[
            "Views open on clear days.",
            "Weather shifts with ridges.",
            "Terraces mark old labor.",
            "Forests thin with height.",
            "Echoes carry between slopes.",
        ],
    ),
    ElevationBand.HIGHLAND: ElevationBandInfo(
        label="Highland",
        description="High country — thin air and exposed stone.",
        flavor=[
            "Wind owns the ridges.",
            "Trees shrink to scrub.",
            "Nights turn sharp quickly.",
            "Clouds brush the shoulders.",
            "Stone outcrops like bones.",
        ],
    ),
    ElevationBand.LOFTY: ElevationBandInfo(
        label="Lofty",
        description="Towering elevation where only hard things thrive.",
        flavor=[
            "Breath shortens on climbs.",
            "Snow lingers in pockets.",
            "Eagles seem at eye level.",
            "Paths are narrow and cruel.",
            "The world spreads below.",
        ],
    ),
    ElevationBand.SUMMIT: ElevationBandInfo(
        label="Summit",
        description="Peaks and crests — sky, stone, and little else.",
        flavor=[
            "Air tastes thin and clean.",
            "Ice survives into summer.",
            "Storms arrive without warning.",
            "Every direction is down.",
            "Silence feels absolute.",
        ],
    ),
}
