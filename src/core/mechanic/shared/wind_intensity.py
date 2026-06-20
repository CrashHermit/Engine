from src.core.model.environment.shared.wind_intensity import (
    BREAKPOINTS,
    ORDER,
    WindIntensityBand,
)


class WindIntensity:
    def windintensity_band(self, value: float) -> WindIntensityBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def windintensity_index(self, band: WindIntensityBand) -> int:
        return ORDER.index(band)
