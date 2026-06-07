"""Biome resolution from climate and terrain."""

from __future__ import annotations

import pytest

from src.core.model.biome import BIOME_MATRIX, Biome, BiomeMatrix
from src.core.model.climate import Precipitation, Temperature
from src.core.model.terrain import (
    SHORE_HYDROLOGY,
    Depth,
    Elevation,
    Hydrology,
    WaterDepth,
)


def _surface(temperature: Temperature, precipitation: Precipitation) -> Biome:
    """Resolve a dry-land climate band pair at the default (midland) elevation."""
    return BIOME_MATRIX.resolve(
        temperature=temperature,
        precipitation=precipitation,
        elevation=Elevation.MIDLAND,
        hydrology=Hydrology.NONE,
    )


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
        BIOME_MATRIX.resolve(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.LOWLAND,
            hydrology=hydrology,
            water_depth=WaterDepth.DEEP,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("hydrology", "expected"),
    [
        (Hydrology.BEACH, Biome.BEACH),
        (Hydrology.CLIFF, Biome.SEA_CLIFF),
        (Hydrology.HEADLAND, Biome.HEADLAND),
        (Hydrology.TIDAL_FLAT, Biome.TIDAL_FLAT),
    ],
)
def test_shore_hydrology_biome(hydrology: Hydrology, expected: Biome) -> None:
    assert (
        BIOME_MATRIX.resolve(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.LOWLAND,
            hydrology=hydrology,
        )
        == expected
    )


def test_shore_biome_ignores_elevation() -> None:
    """A cliff is a sea cliff whether it meets the water low or high."""
    low = BIOME_MATRIX.resolve(
        temperature=Temperature.MILD,
        precipitation=Precipitation.WET,
        elevation=Elevation.LOWLAND,
        hydrology=Hydrology.CLIFF,
    )
    high = BIOME_MATRIX.resolve(
        temperature=Temperature.MILD,
        precipitation=Precipitation.WET,
        elevation=Elevation.SUMMIT,
        hydrology=Hydrology.CLIFF,
    )
    assert low == high == Biome.SEA_CLIFF


def test_cliff_over_ocean_at_highland_is_sea_cliff_not_montane_forest() -> None:
    assert (
        BIOME_MATRIX.resolve(
            temperature=Temperature.MILD,
            precipitation=Precipitation.WET,
            elevation=Elevation.HIGHLAND,
            hydrology=Hydrology.CLIFF,
        )
        == Biome.SEA_CLIFF
    )


def test_estuary_hydrology_is_estuary() -> None:
    assert (
        BIOME_MATRIX.resolve(
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
        BIOME_MATRIX.resolve(
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
        BIOME_MATRIX.resolve(
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
        BIOME_MATRIX.resolve(
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
        BIOME_MATRIX.resolve(
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
        BIOME_MATRIX.resolve(
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
        BIOME_MATRIX.resolve(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.MIDLAND,
            hydrology=Hydrology.LAKE,
            water_depth=WaterDepth.DEEP,
            depth=Depth.LOW,
        )
        == Biome.LAKE
    )


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        (Depth.SUBGRADE, Biome.CRYPT),
        (Depth.SHALLOW, Biome.CELLAR),
        (Depth.LOW, Biome.CAVERN),
        (Depth.DEEP, Biome.DEEP_CAVERN),
        (Depth.ABYSSAL, Biome.ABYSS),
    ],
)
def test_depth_resolves_subterranean_biome(depth: Depth, expected: Biome) -> None:
    assert (
        BIOME_MATRIX.resolve(
            temperature=Temperature.MILD,
            precipitation=Precipitation.SEASONAL,
            elevation=Elevation.MIDLAND,
            depth=depth,
        )
        == expected
    )


def test_inland_lowland_wet_is_not_shore_biome() -> None:
    assert (
        BIOME_MATRIX.resolve(
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
        _surface(temperature, precipitation)
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
        _surface(temperature, precipitation)
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
    assert _surface(temperature, precipitation) == expected


def test_band_centre_anchors_reproduce_the_climate_grid() -> None:
    """Midland nearest-anchor resolution matches a direct climate-grid lookup."""
    for (temperature, precipitation), expected in BiomeMatrix._SURFACE_GRID.items():
        assert _surface(temperature, precipitation) == expected


@pytest.mark.parametrize(
    ("temperature", "precipitation", "elevation", "expected"),
    [
        (
            Temperature.FREEZING,
            Precipitation.SEASONAL,
            Elevation.SUMMIT,
            Biome.GLACIER,
        ),
        (
            Temperature.COOL,
            Precipitation.SEASONAL,
            Elevation.SUMMIT,
            Biome.ALPINE_TUNDRA,
        ),
        (
            Temperature.MILD,
            Precipitation.WET,
            Elevation.HIGHLAND,
            Biome.MONTANE_FOREST,
        ),
        (
            Temperature.COOL,
            Precipitation.DELUGE,
            Elevation.HIGHLAND,
            Biome.MOOR,
        ),
    ],
)
def test_elevation_biomes_resolve_at_their_anchors(
    temperature: Temperature,
    precipitation: Precipitation,
    elevation: Elevation,
    expected: Biome,
) -> None:
    """The four elevation biomes win at their high-elevation anchor points."""
    assert (
        BIOME_MATRIX.resolve(
            temperature=temperature,
            precipitation=precipitation,
            elevation=elevation,
            hydrology=Hydrology.NONE,
        )
        == expected
    )


def test_default_elevation_keeps_the_climate_biome() -> None:
    """A forest at the midland default stays its climate biome, not montane."""
    assert _surface(Temperature.MILD, Precipitation.SEASONAL) == Biome.TEMPERATE_FOREST


def test_aquatic_grid_covers_every_water_body_and_temperature() -> None:
    """The aquatic grid is square: every water body × temperature pair is set."""
    water = [
        hydrology
        for hydrology in Hydrology
        if hydrology not in SHORE_HYDROLOGY and hydrology != Hydrology.NONE
    ]
    expected = {
        (hydrology, temperature) for hydrology in water for temperature in Temperature
    }
    assert set(BiomeMatrix._AQUATIC_GRID) == expected


@pytest.mark.parametrize("precipitation", list(Precipitation))
def test_shallow_warm_sea_is_coral_regardless_of_precipitation(
    precipitation: Precipitation,
) -> None:
    """Shallow warm seas reef on temperature alone; rainfall no longer matters."""
    assert (
        BIOME_MATRIX.resolve(
            temperature=Temperature.WARM,
            precipitation=precipitation,
            elevation=Elevation.LOWLAND,
            hydrology=Hydrology.SEA,
            water_depth=WaterDepth.SHALLOW,
        )
        == Biome.CORAL_REEF
    )
