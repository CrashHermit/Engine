from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.wind_intensity import (
    BREAKPOINTS,
    INFO,
    ORDER,
    WindIntensityBand,
    WindIntensityBandInfo,
)


@dataclass
class WindIntensityProfile:
    value: float
    band: WindIntensityBand
    label: str
    description: str


class WindIntensity:
    def windintensity_band(self, value: float) -> WindIntensityBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def windintensity_index(self, band: WindIntensityBand) -> int:
        return ORDER.index(band)

    def windintensity_info(self, value: float) -> WindIntensityBandInfo:
        return INFO[self.windintensity_band(value)]

    def windintensity_profile(self, value: float) -> WindIntensityProfile:
        band: WindIntensityBand = self.windintensity_band(value)
        info: WindIntensityBandInfo = INFO[band]
        return WindIntensityProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def windintensity_describe(self, value: float) -> str:
        return self.windintensity_info(value).description

    def windintensity_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.windintensity_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for wind intensity band {self.windintensity_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
