from src.core.model.environment.weather.humidity import (
    BREAKPOINTS,
    ORDER,
    HumidityBand,
)


class Humidity:
    def humidity_band(self, value: float) -> HumidityBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def humidity_index(self, band: HumidityBand) -> int:
        return ORDER.index(band)
