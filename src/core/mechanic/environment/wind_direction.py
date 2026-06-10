from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.wind_direction import (
    BREAKPOINTS,
    INFO,
    ORDER,
    WindDirectionBand,
    WindDirectionBandInfo,
)


@dataclass
class WindDirectionProfile:
    value: float
    band: WindDirectionBand
    label: str
    description: str


class WindDirection:
    def winddirection_band(self, value: float) -> WindDirectionBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def winddirection_index(self, band: WindDirectionBand) -> int:
        return ORDER.index(band)

    def winddirection_info(self, value: float) -> WindDirectionBandInfo:
        return INFO[self.winddirection_band(value)]

    def winddirection_profile(self, value: float) -> WindDirectionProfile:
        band: WindDirectionBand = self.winddirection_band(value)
        info: WindDirectionBandInfo = INFO[band]
        return WindDirectionProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def winddirection_describe(self, value: float) -> str:
        return self.winddirection_info(value).description

    def winddirection_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.winddirection_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for wind direction band {self.winddirection_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
