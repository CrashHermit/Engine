from src.core.model.environment.shared.temperature import (
    BREAKPOINTS,
    ORDER,
    TemperatureBand,
)


class Temperature:
    def temperature_band(self, value: float) -> TemperatureBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def temperature_index(self, band: TemperatureBand) -> int:
        return ORDER.index(band)
