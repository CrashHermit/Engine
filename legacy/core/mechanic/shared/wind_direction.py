from src.core.model.environment.shared.wind_direction import (
    BREAKPOINTS,
    ORDER,
    WindDirectionBand,
)


class WindDirection:
    def winddirection_band(self, value: float) -> WindDirectionBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def winddirection_index(self, band: WindDirectionBand) -> int:
        return ORDER.index(band)
