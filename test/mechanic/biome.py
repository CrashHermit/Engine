"""Biome resolution from climate and terrain."""

from __future__ import annotations

import pytest

from src.core.model.biome import Biome, biome_from
from src.core.model.climate import Precipitation, Temperature
from src.core.model.terrain import (
    Elevation,
    Salinity,
    WaterDepth,
    WaterForm,
    default_salinity,
)


@pytest.mark.parametrize(
    ("water_form", "expected"),
    [
        (WaterForm.STREAM, Biome.BROOK),
        (WaterForm.RIVER, Biome.RIVER),
        (WaterForm.LAKE, Biome.LAKE),
        (WaterForm.SEA, Biome.LITTORAL),
        (WaterForm.OCEAN, Biome.OPEN_OCEAN),
    ],
)
def test_water_form_default_salinity_biome(
    water_form: WaterForm, expected: Biome
) -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.LOWLAND,
            water_form=water_form,
            water_depth=WaterDepth.DEEP,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("water_form", "expected"),
    [
        (WaterForm.STREAM, Salinity.FRESH),
        (WaterForm.RIVER, Salinity.FRESH),
        (WaterForm.LAKE, Salinity.FRESH),
        (WaterForm.SEA, Salinity.SALT),
        (WaterForm.OCEAN, Salinity.SALT),
    ],
)
def test_default_salinity_for_water_form(
    water_form: WaterForm, expected: Salinity
) -> None:
    assert default_salinity(water_form) == expected


def test_brackish_river_is_estuary() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.RIVER,
            salinity=Salinity.BRACKISH,
            water_depth=WaterDepth.MODERATE,
        )
        == Biome.ESTUARY
    )


def test_salt_river_is_estuary() -> None:
    assert (
        biome_from(
            temperature=Temperature.WARM,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.RIVER,
            salinity=Salinity.SALT,
            water_depth=WaterDepth.MODERATE,
        )
        == Biome.ESTUARY
    )


def test_fresh_ocean_is_inland_sea_lake() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.OCEAN,
            salinity=Salinity.FRESH,
            water_depth=WaterDepth.VERY_DEEP,
        )
        == Biome.LAKE
    )


def test_frozen_river_is_ice_shelf() -> None:
    assert (
        biome_from(
            temperature=Temperature.FREEZING,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.RIVER,
            water_depth=WaterDepth.DEEP,
        )
        == Biome.ICE_SHELF
    )


def test_frozen_sea_is_polar_sea() -> None:
    assert (
        biome_from(
            temperature=Temperature.FREEZING,
            precipitation=Precipitation.DRY,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.SEA,
            water_depth=WaterDepth.DEEP,
        )
        == Biome.POLAR_SEA
    )


def test_shallow_cool_wet_sea_is_kelp_forest() -> None:
    assert (
        biome_from(
            temperature=Temperature.COOL,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.SEA,
            water_depth=WaterDepth.SHALLOW,
        )
        == Biome.KELP_FOREST
    )


def test_shallow_warm_wet_sea_is_coral_reef() -> None:
    assert (
        biome_from(
            temperature=Temperature.WARM,
            precipitation=Precipitation.DELUGE,
            elevation=Elevation.LOWLAND,
            water_form=WaterForm.SEA,
            water_depth=WaterDepth.SHALLOW,
        )
        == Biome.CORAL_REEF
    )


def test_water_form_overrides_underground() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.DEEP,
            water_form=WaterForm.LAKE,
            water_depth=WaterDepth.DEEP,
        )
        == Biome.LAKE
    )


def test_coastal_on_lowland_wet_coast_flag() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            coastal=True,
        )
        == Biome.COASTAL
    )


def test_coastal_requires_coast_flag() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            coastal=False,
        )
        == Biome.TEMPERATE_RAINFOREST
    )
