"""Biome resolution from climate."""

from __future__ import annotations

import pytest

from core.model.climate.biome import BIOME_MATRIX, Biome, Biome
from core.model.climate.precipitation import PrecipitationEnum, PrecipitationData
from core.model.temperature import Temperature, TemperatureData


def test_climate_grid_yields_49_distinct_biomes() -> None:
    """Every temperature × precipitation band pair maps to a distinct biome."""
    results = {
        _resolve(temperature, precipitation)
        for temperature in Temperature
        for precipitation in PrecipitationEnum
    }
    assert len(results) == 49


@pytest.mark.parametrize(
    ("temperature", "precipitation", "expected"),
    [
        (Temperature.FRIGID, PrecipitationEnum.HYPER_ARID, Biome.ICE_SHEET),
        (Temperature.FRIGID, PrecipitationEnum.SATURATED, Biome.MELTING_PACK),
        (Temperature.FREEZING, PrecipitationEnum.HYPER_ARID, Biome.COLD_DESERT),
        (Temperature.COOL, PrecipitationEnum.SATURATED, Biome.FEN_WETLAND),
        (Temperature.MILD, PrecipitationEnum.HYPER_HUMID, Biome.TEMPERATE_RAINFOREST),
        (Temperature.WARM, PrecipitationEnum.ARID, Biome.THORN_SCRUB),
        (Temperature.HOT, PrecipitationEnum.HYPER_ARID, Biome.SAND_DESERT),
        (Temperature.SCORCHING, PrecipitationEnum.SATURATED, Biome.FLOODED_JUNGLE),
    ],
)
def test_sample_climate_cells(
    temperature: Temperature, precipitation: PrecipitationEnum, expected: Biome
) -> None:
    assert _resolve(temperature, precipitation) == expected


def test_climate_grid_lookup() -> None:
    """Each temperature × precipitation pair maps directly to its grid biome."""
    for (temperature, precipitation), expected in Biome.biome_grid.items():
        assert _resolve(temperature, precipitation) == expected


def test_biome_matrix_singleton_matches_class_grid() -> None:
    for (temperature, precipitation), expected in Biome.biome_grid.items():
        assert (
            BIOME_MATRIX.resolve_biome(
                TemperatureData(temperature=temperature),
                PrecipitationData(precipitation=precipitation),
            )
            == expected
        )


def _resolve(temperature: Temperature, precipitation: PrecipitationEnum) -> Biome:
    return BIOME_MATRIX.resolve_biome(
        TemperatureData(temperature=temperature),
        PrecipitationData(precipitation=precipitation),
    )
