"""Particulate type lookup from biome and wind."""

from __future__ import annotations

import pytest
from core.model.climate.biome import Biome
from core.model.weather.particulate_type import ParticulateType, ParticulateTypeEnum
from core.model.weather.wind_intensity import WindIntensityEnum


def test_grid_has_343_entries() -> None:
    assert len(ParticulateType.particulate_type_grid) == 343


def test_grid_covers_all_biome_wind_pairs() -> None:
    expected = {(biome, wind) for biome in Biome for wind in WindIntensityEnum}
    assert set(ParticulateType.particulate_type_grid.keys()) == expected


def test_all_non_none_types_appear() -> None:
    active = {
        value
        for value in ParticulateType.particulate_type_grid.values()
        if value != ParticulateTypeEnum.NONE
    }
    assert active == {
        ParticulateTypeEnum.DUST,
        ParticulateTypeEnum.SAND,
        ParticulateTypeEnum.ASH,
        ParticulateTypeEnum.SMOKE,
        ParticulateTypeEnum.SPORES,
        ParticulateTypeEnum.POLLEN,
    }


@pytest.mark.parametrize(
    "wind",
    [WindIntensityEnum.CALM, WindIntensityEnum.GENTLE],
)
def test_low_wind_suppresses_sand_biomes(wind: WindIntensityEnum) -> None:
    pt = ParticulateType()
    assert pt.get_particulate_type(Biome.SAND_DESERT, wind) == ParticulateTypeEnum.NONE


@pytest.mark.parametrize(
    "wind",
    [
        WindIntensityEnum.BREEZY,
        WindIntensityEnum.BLUSTERY,
        WindIntensityEnum.GALE,
        WindIntensityEnum.STORM,
        WindIntensityEnum.HURRICANE,
    ],
)
def test_higher_wind_lifts_sand_in_desert(wind: WindIntensityEnum) -> None:
    pt = ParticulateType()
    assert pt.get_particulate_type(Biome.SAND_DESERT, wind) == ParticulateTypeEnum.SAND


@pytest.mark.parametrize("wind", list(WindIntensityEnum))
def test_none_biomes_stay_clear(wind: WindIntensityEnum) -> None:
    pt = ParticulateType()
    assert pt.get_particulate_type(Biome.ICE_SHEET, wind) == ParticulateTypeEnum.NONE
    assert pt.get_particulate_type(Biome.DENSE_TAIGA, wind) == ParticulateTypeEnum.NONE


def test_cold_desert_ash_at_breezy_plus() -> None:
    pt = ParticulateType()
    assert (
        pt.get_particulate_type(Biome.COLD_DESERT, WindIntensityEnum.CALM)
        == ParticulateTypeEnum.NONE
    )
    assert (
        pt.get_particulate_type(Biome.COLD_DESERT, WindIntensityEnum.BREEZY)
        == ParticulateTypeEnum.ASH
    )
