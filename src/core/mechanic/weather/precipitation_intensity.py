from __future__ import annotations

from src.core.model.environment.weather.cloud_cover import CloudCoverBand
from src.core.model.environment.weather.humidity import HumidityBand
from src.core.model.environment.weather.precipitation_intensity import (
    BREAKPOINTS,
    INTENSITY_GRID,
    ORDER,
    PrecipitationIntensityBand,
)


class PrecipitationIntensity:
    def precipitationintensity_band(self, value: float) -> PrecipitationIntensityBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def precipitationintensity_index(self, band: PrecipitationIntensityBand) -> int:
        return ORDER.index(band)

    def precipitationintensity_from_weather(
        self,
        cloud_cover: CloudCoverBand,
        humidity: HumidityBand,
    ) -> PrecipitationIntensityBand:
        return INTENSITY_GRID.get(
            (cloud_cover, humidity), PrecipitationIntensityBand.NONE
        )
