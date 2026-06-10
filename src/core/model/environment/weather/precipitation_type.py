from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.temperature import TemperatureBand
from src.core.model.environment.weather.precipitation_intensity import (
    PrecipitationIntensityBand,
)


class PrecipitationTypeEnum(StrEnum):
    NONE = "none"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    FREEZING_RAIN = "freezing_rain"
    GRAUPEL = "graupel"
    HAIL = "hail"


@dataclass(frozen=True)
class PrecipitationTypeInfo:
    label: str
    description: str
    flavor: list[str]


INFO: dict[PrecipitationTypeEnum, PrecipitationTypeInfo] = {
    PrecipitationTypeEnum.NONE: PrecipitationTypeInfo(
        label="None",
        description="No precipitation falling.",
        flavor=[
            "The sky offers nothing wet.",
            "Ground stays as it was.",
            "Gear remains dry.",
            "Only wind or stillness fills the air.",
            "Pools hold their last level.",
        ],
    ),
    PrecipitationTypeEnum.RAIN: PrecipitationTypeInfo(
        label="Rain",
        description="Liquid water falling from the clouds.",
        flavor=[
            "Rhythm on stone and leaf.",
            "Petrichor rises from soil.",
            "Cloth darkens at the shoulders.",
            "Rivulets find the lowest path.",
            "Puddles spread by degrees.",
        ],
    ),
    PrecipitationTypeEnum.SNOW: PrecipitationTypeInfo(
        label="Snow",
        description="Frozen crystals drifting down.",
        flavor=[
            "Flakes melt on exposed skin.",
            "Sound muffles under fresh cover.",
            "Breath hangs in the air.",
            "Edges soften under white.",
            "Footsteps crunch or sink.",
        ],
    ),
    PrecipitationTypeEnum.SLEET: PrecipitationTypeInfo(
        label="Sleet",
        description="Ice pellets mixed with rain.",
        flavor=[
            "Tiny impacts rattle on metal.",
            "Surfaces glaze dangerously.",
            "Each gust stings exposed skin.",
            "Neither fully rain nor snow.",
            "Footing turns treacherous fast.",
        ],
    ),
    PrecipitationTypeEnum.FREEZING_RAIN: PrecipitationTypeInfo(
        label="Freezing rain",
        description="Rain that freezes on contact.",
        flavor=[
            "Branches gleam with ice.",
            "Every step risks a fall.",
            "A cold skin coats stone.",
            "Warmth cannot reach the ground.",
            "The world turns slick and sharp.",
        ],
    ),
    PrecipitationTypeEnum.GRAUPEL: PrecipitationTypeInfo(
        label="Graupel",
        description="Soft, rimed pellets of snow.",
        flavor=[
            "Small white beads bounce on impact.",
            "Less dense than hail, colder than rain.",
            "Drifts look rough and granular.",
            "Melts quickly on skin.",
            "Skies feel unsettled.",
        ],
    ),
    PrecipitationTypeEnum.HAIL: PrecipitationTypeInfo(
        label="Hail",
        description="Hard ice stones falling from storm clouds.",
        flavor=[
            "Impacts drum on roofs.",
            "Animals flee for cover.",
            "Leaves shred under strikes.",
            "White stones bounce and roll.",
            "Shelter becomes urgent.",
        ],
    ),
}

PRECIPITATION_TYPE_GRID: dict[
    tuple[TemperatureBand, PrecipitationIntensityBand], PrecipitationTypeEnum
] = {
        # â”€â”€ FRIGID â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FRIGID,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.SNOW,
        # â”€â”€ FREEZING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.FREEZING,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.SNOW,
        # â”€â”€ COOL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.SLEET,
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.GRAUPEL,
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.GRAUPEL,
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureBand.COOL,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.SNOW,
        # â”€â”€ MILD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.SLEET,
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.FREEZING_RAIN,
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.FREEZING_RAIN,
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.MILD,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.HAIL,
        # â”€â”€ WARM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.WARM,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.HAIL,
        # â”€â”€ HOT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.HAIL,
        (
            TemperatureBand.HOT,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.HAIL,
        # â”€â”€ SCORCHING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.DRIZZLE,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.LIGHT,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.STEADY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.TORRENTIAL,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureBand.SCORCHING,
            PrecipitationIntensityBand.CLOUDBURST,
        ): PrecipitationTypeEnum.RAIN,
    }
