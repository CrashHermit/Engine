from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.climate.biome import (
    BIOME_GRID,
    INFO,
    BiomeEnum,
    BiomeEnumInfo,
)
from src.core.model.environment.climate.precipitation import PrecipitationBand
from src.core.model.environment.temperature import TemperatureBand


@dataclass
class BiomeProfile:
    band: BiomeEnum
    label: str
    description: str


class Biome:
    def biome_from_climate(
        self,
        temperature: TemperatureBand,
        precipitation: PrecipitationBand,
    ) -> BiomeEnum:
        return BIOME_GRID[(temperature, precipitation)]

    def biome_info(self, band: BiomeEnum) -> BiomeEnumInfo:
        return INFO[band]

    def biome_profile(self, band: BiomeEnum) -> BiomeProfile:
        info: BiomeEnumInfo = INFO[band]
        return BiomeProfile(
            band=band,
            label=info.label,
            description=info.description,
        )

    def biome_describe(self, band: BiomeEnum) -> str:
        return INFO[band].description

    def biome_flavor(self, band: BiomeEnum, rng: Random | None = None) -> str:
        flavors: list[str] = INFO[band].flavor
        if not flavors:
            raise ValueError(f"No flavor lines for biome {band!r}")
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
