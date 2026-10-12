from enum import StrEnum

from src.core.model.environment.shared.temperature import TemperatureBand
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


PRECIPITATION_TYPE_GRID: dict[
    tuple[TemperatureBand, PrecipitationIntensityBand], PrecipitationTypeEnum
] = {
    # fmt: off
    # -- FRIGID --
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
    # -- FREEZING --
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
    # -- COOL --
    (TemperatureBand.COOL, PrecipitationIntensityBand.NONE): PrecipitationTypeEnum.NONE,
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
    # -- MILD --
    (TemperatureBand.MILD, PrecipitationIntensityBand.NONE): PrecipitationTypeEnum.NONE,
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
    # -- WARM --
    (TemperatureBand.WARM, PrecipitationIntensityBand.NONE): PrecipitationTypeEnum.NONE,
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
    # -- HOT --
    (TemperatureBand.HOT, PrecipitationIntensityBand.NONE): PrecipitationTypeEnum.NONE,
    (
        TemperatureBand.HOT,
        PrecipitationIntensityBand.DRIZZLE,
    ): PrecipitationTypeEnum.RAIN,
    (TemperatureBand.HOT, PrecipitationIntensityBand.LIGHT): PrecipitationTypeEnum.RAIN,
    (
        TemperatureBand.HOT,
        PrecipitationIntensityBand.STEADY,
    ): PrecipitationTypeEnum.RAIN,
    (TemperatureBand.HOT, PrecipitationIntensityBand.HEAVY): PrecipitationTypeEnum.RAIN,
    (
        TemperatureBand.HOT,
        PrecipitationIntensityBand.TORRENTIAL,
    ): PrecipitationTypeEnum.HAIL,
    (
        TemperatureBand.HOT,
        PrecipitationIntensityBand.CLOUDBURST,
    ): PrecipitationTypeEnum.HAIL,
    # -- SCORCHING --
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
    # fmt: on
}
