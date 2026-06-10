from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.weather.cloud_cover import (
    BREAKPOINTS,
    INFO,
    ORDER,
    CloudCoverBand,
    CloudCoverBandInfo,
)


@dataclass
class CloudCoverProfile:
    value: float
    band: CloudCoverBand
    label: str
    description: str


class CloudCover:
    def cloudcover_band(self, value: float) -> CloudCoverBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def cloudcover_index(self, band: CloudCoverBand) -> int:
        return ORDER.index(band)

    def cloudcover_info(self, value: float) -> CloudCoverBandInfo:
        return INFO[self.cloudcover_band(value)]

    def cloudcover_profile(self, value: float) -> CloudCoverProfile:
        band: CloudCoverBand = self.cloudcover_band(value)
        info: CloudCoverBandInfo = INFO[band]
        return CloudCoverProfile(
            value=value,
            band=band,
            label=info.label,
            description=info.description,
        )

    def cloudcover_describe(self, value: float) -> str:
        return self.cloudcover_info(value).description

    def cloudcover_flavor(self, value: float, rng: Random | None = None) -> str:
        flavors: list[str] = self.cloudcover_info(value).flavor
        if not flavors:
            raise ValueError(
                f"No flavor lines for cloud cover band {self.cloudcover_band(value)!r}"
            )
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
