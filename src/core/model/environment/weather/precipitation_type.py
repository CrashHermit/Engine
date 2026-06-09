from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.temperature import TemperatureEnum
from src.core.model.environment.weather.precipitation_intensity import (
    PrecipitationIntensityEnum,
)


class PrecipitationTypeEnum(StrEnum):
    NONE = "none"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    FREEZING_RAIN = "freezing_rain"
    GRAUPEL = "graupel"
    HAIL = "hail"


@dataclass
class PrecipitationTypeData:
    precipitation_type: PrecipitationTypeEnum


class PrecipitationType:
    """Map weather temperature and precipitation intensity to a precipitation type."""

    precipitation_type_grid: dict[
        tuple[TemperatureEnum, PrecipitationIntensityEnum], PrecipitationTypeEnum
    ] = {
        # ── FRIGID ────────────────────────────────────────────────────────────
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FRIGID,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.SNOW,
        # ── FREEZING ──────────────────────────────────────────────────────────
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.FREEZING,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.SNOW,
        # ── COOL ──────────────────────────────────────────────────────────────
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.SLEET,
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.GRAUPEL,
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.GRAUPEL,
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.SNOW,
        (
            TemperatureEnum.COOL,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.SNOW,
        # ── MILD ──────────────────────────────────────────────────────────────
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.SLEET,
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.FREEZING_RAIN,
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.FREEZING_RAIN,
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.MILD,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.HAIL,
        # ── WARM ──────────────────────────────────────────────────────────────
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.WARM,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.HAIL,
        # ── HOT ───────────────────────────────────────────────────────────────
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.HAIL,
        (
            TemperatureEnum.HOT,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.HAIL,
        # ── SCORCHING ───────────────────────────────────────────────────────
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.NONE,
        ): PrecipitationTypeEnum.NONE,
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.DRIZZLE,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.LIGHT,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.STEADY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.HEAVY,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.TORRENTIAL,
        ): PrecipitationTypeEnum.RAIN,
        (
            TemperatureEnum.SCORCHING,
            PrecipitationIntensityEnum.CLOUDBURST,
        ): PrecipitationTypeEnum.RAIN,
    }

    def get_precipitation_type(
        self,
        temperature_enum: TemperatureEnum,
        intensity_enum: PrecipitationIntensityEnum,
    ) -> PrecipitationTypeEnum:
        """Look up the precipitation type for a temperature and intensity pair."""
        return self.precipitation_type_grid.get(
            (temperature_enum, intensity_enum), PrecipitationTypeEnum.NONE
        )
