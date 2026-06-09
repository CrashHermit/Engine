"""Scene context composition."""

from __future__ import annotations

import pytest

from src.core.helper.scene_context import SceneContextHelper
from src.core.model.biome import Biome
from src.core.model.climate import (
    ClimateData,
    Temperature,
)
from src.core.model.climate import (
    Precipitation as ClimatePrecipitation,
)
from src.core.model.environment import EnvironmentData
from src.core.model.location import LocationData
from src.core.model.terrain import Elevation, TerrainData
from src.core.model.weather import (
    Humidity,
    WeatherData,
    WindDirection,
    WindSpeed,
)
from src.core.model.weather import (
    Precipitation as WeatherPrecipitation,
)


@pytest.fixture
def helper() -> SceneContextHelper:
    return SceneContextHelper()


def _sample_location() -> LocationData:
    return LocationData(
        id="north-trail",
        name="North Trail",
        description="A highland path.",
        environment=EnvironmentData(
            climate=ClimateData(
                temperature=Temperature.MILD,
                precipitation=ClimatePrecipitation.WET,
            ),
            terrain=TerrainData(elevation=Elevation.HIGHLAND),
        ),
        weather=WeatherData(
            humidity=Humidity.CRISP,
            precipitation=WeatherPrecipitation.DRIZZLE,
            wind_direction=WindDirection.NORTH_WEST,
            wind_speed=WindSpeed.BREEZY,
        ),
    )


def test_resolve_location_biome(helper: SceneContextHelper) -> None:
    assert (
        helper.resolve_location_biome(_sample_location()) == Biome.TEMPERATE_RAINFOREST
    )


def test_compose_location_structured(helper: SceneContextHelper) -> None:
    structured = helper.compose_location_structured(_sample_location())
    assert structured["location_id"] == "north-trail"
    assert structured["biome"]["value"] == "temperate_rainforest"
    assert structured["weather"]["wind_speed"]["value"] == "breezy"
    assert structured["environment"]["terrain"]["elevation"]["value"] == "highland"


def test_compose_location_prose_includes_sections(helper: SceneContextHelper) -> None:
    prose = helper.compose_location_prose(_sample_location())
    assert "Location: north-trail" in prose
    assert "Biome:" in prose
    assert "Humidity:" in prose
    assert "Elevation:" in prose


def test_compose_location_yaml(helper: SceneContextHelper) -> None:
    yaml_text = helper.compose_location_yaml(_sample_location())
    assert "location_id: north-trail" in yaml_text
    assert "biome:" in yaml_text
    assert "weather:" in yaml_text
