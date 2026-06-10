from __future__ import annotations

from src.core.model.environment.terrain.elevation import (
    BREAKPOINTS,
    ORDER,
    ElevationBand,
)


class Elevation:
    def elevation_band(self, value: float) -> ElevationBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def elevation_index(self, band: ElevationBand) -> int:
        return ORDER.index(band)
