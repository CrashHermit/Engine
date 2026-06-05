"""Biome resolution from climate and terrain."""

from __future__ import annotations

import pytest

from src.core.model.biome import Biome, biome_from
from src.core.model.climate import Precipitation, Temperature
from src.core.model.terrain import Elevation, Hydrology, WaterDepth


@pytest.mark.parametrize(
    ("hydrology", "expected"),
    [
        (Hydrology.STREAM, Biome.BROOK),
        (Hydrology.RIVER, Biome.RIVER),
        (Hydrology.LAKE, Biome.LAKE),
        (Hydrology.SEA, Biome.LITTORAL),
        (Hydrology.OCEAN, Biome.OPEN_OCEAN),
    ],
)
def test_hydrology_grid_biome(hydrology: Hydrology, expected: Biome) -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.LOWLAND,
            hydrology=hydrology,
            water_depth=WaterDepth.DEEP,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("hydrology", "elevation", "expected"),
    [
        (Hydrology.BEACH, Elevation.LOWLAND, Biome.BEACH),
        (Hydrology.BEACH, Elevation.ROLLING, Biome.BEACH),
        (Hydrology.CLIFF, Elevation.LOWLAND, Biome.SEA_CLIFF),
        (Hydrology.CLIFF, Elevation.HIGHLAND, Biome.SEA_CLIFF),
        (Hydrology.CLIFF, Elevation.ALPINE, Biome.SEA_CLIFF),
        (Hydrology.HEADLAND, Elevation.LOWLAND, Biome.HEADLAND),
        (Hydrology.HEADLAND, Elevation.HIGHLAND, Biome.HEADLAND),
        (Hydrology.TIDAL_FLAT, Elevation.LOWLAND, Biome.TIDAL_FLAT),
        (Hydrology.TIDAL_FLAT, Elevation.BASIN, Biome.TIDAL_FLAT),
    ],
)
def test_shore_hydrology_elevation_grid(
    hydrology: Hydrology, elevation: Elevation, expected: Biome
) -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=elevation,
            hydrology=hydrology,
        )
        == expected
    )


def test_cliff_over_ocean_at_highland_is_sea_cliff_not_montane_forest() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.HIGHLAND,
            hydrology=Hydrology.CLIFF,
        )
        == Biome.SEA_CLIFF
    )


def test_estuary_hydrology_is_estuary() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            hydrology=Hydrology.ESTUARY,
            water_depth=WaterDepth.MODERATE,
        )
        == Biome.ESTUARY
    )


def test_inland_sea_is_lake() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            hydrology=Hydrology.INLAND_SEA,
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
            hydrology=Hydrology.RIVER,
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
            hydrology=Hydrology.SEA,
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
            hydrology=Hydrology.SEA,
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
            hydrology=Hydrology.SEA,
            water_depth=WaterDepth.SHALLOW,
        )
        == Biome.CORAL_REEF
    )


def test_hydrology_overrides_underground() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.DEEP,
            hydrology=Hydrology.LAKE,
            water_depth=WaterDepth.DEEP,
        )
        == Biome.LAKE
    )


def test_inland_lowland_wet_is_not_shore_biome() -> None:
    assert (
        biome_from(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            hydrology=Hydrology.NONE,
        )
        == Biome.TEMPERATE_RAINFOREST
    )
