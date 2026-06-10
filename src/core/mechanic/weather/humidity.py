from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.weather.humidity import (
    BREAKPOINTS,
    INFO,
    ORDER,
    HumidityBand,
    HumidityBandInfo,
)


@dataclass
class HumidityProfile:
    value: float
    band: HumidityBand
    label: str
    description: str


class Humidity:
    def humidity_band(self, value: float) -> HumidityBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def humidity_index(self, band: HumidityBand) -> int:
        return ORDER.index(band)

    def humidity_info(self, value: float) -> HumidityBandInfo:
        return INFO[self.humidity_band(value)]

    def humidity_profile(self, value: float) -> HumidityProfile:
        band: HumidityBand = self.humidity_band(value)
        info: HumidityBandInfo = INFO[band]
        return HumidityProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def humidity_describe(self, value: float) -> str:
        return self.humidity_info(value).description

    def humidity_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.humidity_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for humidity band {self.humidity_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
