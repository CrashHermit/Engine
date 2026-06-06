"""Biome resolution from climate and terrain."""

from __future__ import annotations

import pytest

from src.core.model.biome import Biome, biome_from, get_surface_biome
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


def test_surface_climate_grid_yields_25_distinct_biomes() -> None:
    """Every temperature × precipitation band pair maps to a distinct biome."""
    results = {
        get_surface_biome(temperature, precipitation)
        for temperature in Temperature
        for precipitation in Precipitation
    }
    assert len(results) == 25


@pytest.mark.parametrize(
    "biome",
    [
        Biome.DESERT,
        Biome.SEMI_DESERT,
        Biome.SAVANNA,
        Biome.TROPICAL_WOODLAND,
        Biome.SEASONAL_JUNGLE,
    ],
)
def test_previously_orphan_warm_biomes_are_reachable(biome: Biome) -> None:
    """The warm band activates the five biomes the old grid never produced."""
    results = {
        get_surface_biome(temperature, precipitation)
        for temperature in Temperature
        for precipitation in Precipitation
    }
    assert biome in results


@pytest.mark.parametrize(
    ("temperature", "precipitation", "expected"),
    [
        (Temperature.WARM, Precipitation.ARID, Biome.DESERT),
        (Temperature.WARM, Precipitation.DELUGE, Biome.SEASONAL_JUNGLE),
        (Temperature.HOT, Precipitation.ARID, Biome.DUNE_SEA),
        (Temperature.HOT, Precipitation.DELUGE, Biome.RAINFOREST),
    ],
)
def test_warm_and_hot_rows_are_distinct(
    temperature: Temperature, precipitation: Precipitation, expected: Biome
) -> None:
    assert get_surface_biome(temperature, precipitation) == expected


def test_band_centre_anchors_reproduce_the_climate_grid() -> None:
    """Nearest-anchor resolution on exact bands matches a direct grid lookup."""
    from src.core.model.biome import _SURFACE_BIOMES_TEMPERATURE_PRECIPITATION_GRID

    for (
        temperature,
        precipitation,
    ), expected in _SURFACE_BIOMES_TEMPERATURE_PRECIPITATION_GRID.items():
        assert get_surface_biome(temperature, precipitation) == expected
