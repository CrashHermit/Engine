from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CloudCoverBand(StrEnum):
    CLEAR = "clear"
    FEW = "few"
    SCATTERED = "scattered"
    BROKEN = "broken"
    MOSTLY = "mostly"
    OVERCAST = "overcast"
    LEADEN = "leaden"


@dataclass(frozen=True)
class CloudCoverBandInfo:
    label: str
    description: str
    flavor: list[str]


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

INFO: dict[CloudCoverBand, CloudCoverBandInfo] = {
    CloudCoverBand.CLEAR: CloudCoverBandInfo(
        label="Clear",
        description="Open sky — sun or stars unobstructed.",
        flavor=[
            "Shadows lie sharp.",
            "Horizons feel distant.",
            "Night air cools fast.",
            "Stars pin the darkness.",
            "Heat pours unfiltered.",
        ],
    ),
    CloudCoverBand.FEW: CloudCoverBandInfo(
        label="Few clouds",
        description="Mostly open sky with scattered wisps.",
        flavor=[
            "Sun warms in patches.",
            "Cloud shadows race ground.",
            "Blue dominates the view.",
            "Weather feels changeable.",
            "Light shifts minute to minute.",
        ],
    ),
    CloudCoverBand.SCATTERED: CloudCoverBandInfo(
        label="Scattered",
        description="Clouds and clear sky share the vault.",
        flavor=[
            "Sun and shade trade places.",
            "Wind shapes slow drifts.",
            "Temperature swings feel wider.",
            "Rain seems possible, not likely.",
            "Light has texture.",
        ],
    ),
    CloudCoverBand.BROKEN: CloudCoverBandInfo(
        label="Broken",
        description="Substantial cloud with gaps of brightness.",
        flavor=[
            "Gloom alternates with glare.",
            "Birds quiet before shifts.",
            "Humidity rises subtly.",
            "Edges of clouds glow.",
            "Mood turns watchful.",
        ],
    ),
    CloudCoverBand.MOSTLY: CloudCoverBandInfo(
        label="Mostly cloudy",
        description="Sky dominated by cloud with rare breaks.",
        flavor=[
            "Day feels dimmer.",
            "Colors mute outdoors.",
            "Dusk arrives early.",
            "Air feels close.",
            "Rain whispers maybe.",
        ],
    ),
    CloudCoverBand.OVERCAST: CloudCoverBandInfo(
        label="Overcast",
        description="Uniform cloud lid — flat light, little shadow.",
        flavor=[
            "Everything looks softer.",
            "Distance hides in gray.",
            "Chill seeps without sun.",
            "Time feels suspended.",
            "Umbrellas seem wise.",
        ],
    ),
    CloudCoverBand.LEADEN: CloudCoverBandInfo(
        label="Leaden",
        description="Heavy, low cloud pressing down.",
        flavor=[
            "Sky feels within reach.",
            "Light drains to pewter.",
            "Pressure sits behind the eyes.",
            "Rain feels inevitable.",
            "The world shrinks to near.",
        ],
    ),
}
