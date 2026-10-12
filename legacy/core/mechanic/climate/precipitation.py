from src.core.model.environment.climate.precipitation import (
    BREAKPOINTS,
    ORDER,
    PrecipitationBand,
)


class Precipitation:
    def precipitation_band(self, value: float) -> PrecipitationBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def precipitation_index(self, band: PrecipitationBand) -> int:
        return ORDER.index(band)
