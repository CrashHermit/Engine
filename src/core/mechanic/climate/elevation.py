from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.climate.elevation import (
    BREAKPOINTS,
    INFO,
    ORDER,
    ElevationBand,
    ElevationBandInfo,
)


@dataclass
class ElevationProfile:
    value: float
    band: ElevationBand
    label: str
    description: str


class Elevation:
    def elevation_band(self, value: float) -> ElevationBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def elevation_index(self, band: ElevationBand) -> int:
        return ORDER.index(band)

    def elevation_info(self, value: float) -> ElevationBandInfo:
        return INFO[self.elevation_band(value)]

    def elevation_profile(self, value: float) -> ElevationProfile:
        band: ElevationBand = self.elevation_band(value)
        info: ElevationBandInfo = INFO[band]
        return ElevationProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def elevation_describe(self, value: float) -> str:
        return self.elevation_info(value).description

    def elevation_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.elevation_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for elevation band {self.elevation_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
