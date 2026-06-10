from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.surroundings.alignment import (
    BREAKPOINTS,
    INFO,
    ORDER,
    AlignmentBand,
    AlignmentBandInfo,
)


@dataclass
class AlignmentProfile:
    value: float
    band: AlignmentBand
    label: str
    description: str


class Alignment:
    def alignment_band(self, value: float) -> AlignmentBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def alignment_index(self, band: AlignmentBand) -> int:
        return ORDER.index(band)

    def alignment_info(self, value: float) -> AlignmentBandInfo:
        return INFO[self.alignment_band(value)]

    def alignment_profile(self, value: float) -> AlignmentProfile:
        band: AlignmentBand = self.alignment_band(value)
        info: AlignmentBandInfo = INFO[band]
        return AlignmentProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def alignment_describe(self, value: float) -> str:
        return self.alignment_info(value).description

    def alignment_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.alignment_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for alignment band {self.alignment_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
