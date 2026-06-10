from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.surroundings.savagery import (
    BREAKPOINTS,
    INFO,
    ORDER,
    SavageryBand,
    SavageryBandInfo,
)


@dataclass
class SavageryProfile:
    value: float
    band: SavageryBand
    label: str
    description: str


class Savagery:
    def savagery_band(self, value: float) -> SavageryBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def savagery_index(self, band: SavageryBand) -> int:
        return ORDER.index(band)

    def savagery_info(self, value: float) -> SavageryBandInfo:
        return INFO[self.savagery_band(value)]

    def savagery_profile(self, value: float) -> SavageryProfile:
        band: SavageryBand = self.savagery_band(value)
        info: SavageryBandInfo = INFO[band]
        return SavageryProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def savagery_describe(self, value: float) -> str:
        return self.savagery_info(value).description

    def savagery_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.savagery_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for savagery band {self.savagery_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
