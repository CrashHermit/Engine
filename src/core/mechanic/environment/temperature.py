from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.temperature import (
    BREAKPOINTS,
    INFO,
    ORDER,
    TemperatureBand,
    TemperatureBandInfo,
)


@dataclass
class TemperatureProfile:
    value: float
    band: TemperatureBand
    label: str
    description: str


class Temperature:
    def temperature_band(self, value: float) -> TemperatureBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def temperature_index(self, band: TemperatureBand) -> int:
        return ORDER.index(band)

    def temperature_info(self, value: float) -> TemperatureBandInfo:
        return INFO[self.temperature_band(value)]

    def temperature_profile(self, value: float) -> TemperatureProfile:
        band: TemperatureBand = self.temperature_band(value)
        info: TemperatureBandInfo = INFO[band]
        return TemperatureProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def temperature_describe(self, value: float) -> str:
        return self.temperature_info(value).description

    def temperature_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.temperature_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for temperature band {self.temperature_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
