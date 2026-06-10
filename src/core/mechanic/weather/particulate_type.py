from __future__ import annotations

from dataclasses import dataclass
from random import Random, choice

from src.core.model.environment.climate.biome import BiomeEnum
from src.core.model.environment.weather.particulate_type import (
    INFO,
    PARTICULATE_TYPE_GRID,
    ParticulateTypeEnum,
    ParticulateTypeInfo,
)
from src.core.model.environment.wind_intensity import WindIntensityBand


@dataclass
class ParticulateTypeProfile:
    band: ParticulateTypeEnum
    label: str
    description: str


class ParticulateType:
    def particulatetype_from_environment(
        self,
        biome: BiomeEnum,
        wind_intensity: WindIntensityBand,
    ) -> ParticulateTypeEnum:
        return PARTICULATE_TYPE_GRID.get(
            (biome, wind_intensity), ParticulateTypeEnum.NONE
        )

    def particulatetype_info(self, band: ParticulateTypeEnum) -> ParticulateTypeInfo:
        return INFO[band]

    def particulatetype_profile(
        self, band: ParticulateTypeEnum
    ) -> ParticulateTypeProfile:
        info: ParticulateTypeInfo = INFO[band]
        return ParticulateTypeProfile(
            band=band,
            label=info.label,
            description=info.description,
        )

    def particulatetype_describe(self, band: ParticulateTypeEnum) -> str:
        return INFO[band].description

    def particulatetype_flavor(
        self, band: ParticulateTypeEnum, rng: Random | None = None
    ) -> str:
        flavors: list[str] = INFO[band].flavor
        if not flavors:
            raise ValueError(f"No flavor lines for particulate type {band!r}")
        if rng is None:
            return choice(flavors)
        return rng.choice(flavors)
