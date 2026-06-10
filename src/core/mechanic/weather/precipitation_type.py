from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.temperature import TemperatureBand
from src.core.model.environment.weather.precipitation_intensity import (
    PrecipitationIntensityBand,
)
from src.core.model.environment.weather.precipitation_type import (
    INFO,
    PRECIPITATION_TYPE_GRID,
    PrecipitationTypeEnum,
    PrecipitationTypeInfo,
)


@dataclass
class PrecipitationTypeProfile:
    band: PrecipitationTypeEnum
    label: str
    description: str


class PrecipitationType:
    def precipitationtype_from_weather(
        self,
        temperature: TemperatureBand,
        intensity: PrecipitationIntensityBand,
    ) -> PrecipitationTypeEnum:
        return PRECIPITATION_TYPE_GRID.get(
            (temperature, intensity), PrecipitationTypeEnum.NONE
        )

    def precipitationtype_info(
        self, band: PrecipitationTypeEnum
    ) -> PrecipitationTypeInfo:
        return INFO[band]

    def precipitationtype_profile(
        self, band: PrecipitationTypeEnum
    ) -> PrecipitationTypeProfile:
        info: PrecipitationTypeInfo = INFO[band]
        return PrecipitationTypeProfile(
            band=band,
            label=info.label,
            description=info.description,
        )

    def precipitationtype_describe(self, band: PrecipitationTypeEnum) -> str:
        return INFO[band].description

    def precipitationtype_flavor(
        self, band: PrecipitationTypeEnum, rng: Random | None = None
    ) -> str:
        flavors: list[str] = INFO[band].flavor
        if not flavors:
            raise ValueError(f"No flavor lines for precipitation type {band!r}")
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
