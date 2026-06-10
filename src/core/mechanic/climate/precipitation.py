from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.climate.precipitation import (
    BREAKPOINTS,
    INFO,
    ORDER,
    PrecipitationBand,
    PrecipitationBandInfo,
)


@dataclass
class PrecipitationProfile:
    value: float
    band: PrecipitationBand
    label: str
    description: str


class Precipitation:
    def precipitation_band(self, value: float) -> PrecipitationBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def precipitation_index(self, band: PrecipitationBand) -> int:
        return ORDER.index(band)

    def precipitation_info(self, value: float) -> PrecipitationBandInfo:
        return INFO[self.precipitation_band(value)]

    def precipitation_profile(self, value: float) -> PrecipitationProfile:
        band: PrecipitationBand = self.precipitation_band(value)
        info: PrecipitationBandInfo = INFO[band]
        return PrecipitationProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def precipitation_describe(self, value: float) -> str:
        return self.precipitation_info(value).description

    def precipitation_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.precipitation_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for precipitation band {self.precipitation_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
