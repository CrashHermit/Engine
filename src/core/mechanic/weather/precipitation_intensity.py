from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.weather.cloud_cover import CloudCoverBand
from src.core.model.environment.weather.humidity import HumidityBand
from src.core.model.environment.weather.precipitation_intensity import (
    BREAKPOINTS,
    INFO,
    INTENSITY_GRID,
    ORDER,
    PrecipitationIntensityBand,
    PrecipitationIntensityBandInfo,
)


@dataclass
class PrecipitationIntensityProfile:
    value: float
    band: PrecipitationIntensityBand
    label: str
    description: str


class PrecipitationIntensity:
    def precipitationintensity_band(self, value: float) -> PrecipitationIntensityBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def precipitationintensity_index(self, band: PrecipitationIntensityBand) -> int:
        return ORDER.index(band)

    def precipitationintensity_info(self, value: float) -> PrecipitationIntensityBandInfo:
        return INFO[self.precipitationintensity_band(value)]

    def precipitationintensity_profile(
        self, value: float
    ) -> PrecipitationIntensityProfile:
        band: PrecipitationIntensityBand = self.precipitationintensity_band(value)
        info: PrecipitationIntensityBandInfo = INFO[band]
        return PrecipitationIntensityProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def precipitationintensity_describe(self, value: float) -> str:
        return self.precipitationintensity_info(value).description

    def precipitationintensity_flavor(
        self, value: float, rng: Random | None = None
    ) -> str:
        flavors: list[str] = self.precipitationintensity_info(value).flavor
        if not flavors:
            raise ValueError(
                "No flavor lines for precipitation intensity band "
                f"{self.precipitationintensity_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)

    def precipitationintensity_from_weather(
        self,
        cloud_cover: CloudCoverBand,
        humidity: HumidityBand,
    ) -> PrecipitationIntensityBand:
        return INTENSITY_GRID.get(
            (cloud_cover, humidity), PrecipitationIntensityBand.NONE
        )
