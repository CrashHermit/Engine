"""Scene context composition."""

from __future__ import annotations

from src.core.helper.scene_context import (
    compose_location_prose,
    compose_location_structured,
    compose_location_yaml,
    resolve_location_biome,
)
from src.core.model.biome import Biome
from src.core.model.climate import (
    ClimateData,
    Precipitation as ClimatePrecipitation,
    Temperature,
)
from src.core.model.environment import EnvironmentData
from src.core.model.location import LocationData
from src.core.model.terrain import Elevation, TerrainData, WaterForm
from src.core.model.weather import (
    Humidity,
    Precipitation as WeatherPrecipitation,
    WeatherData,
    WindDirection,
    WindSpeed,
)


def _sample_location() -> LocationData:
    return LocationData(
        id="north-trail",
        environment=EnvironmentData(
            climate=ClimateData(
                temperature=Temperature.COOL,
                precipitation=ClimatePrecipitation.WET,
            ),
            terrain=TerrainData(
                elevation=Elevation.HIGHLAND,
                water_form=WaterForm.NONE,
                coastal=False,
            ),
        ),
        weather=WeatherData(
            humidity=Humidity.CRISP,
            precipitation=WeatherPrecipitation.DRIZZLE,
            wind_direction=WindDirection.NORTH_WEST,
            wind_speed=WindSpeed.BREEZY,
        ),
    )


def test_resolve_location_biome() -> None:
    assert resolve_location_biome(_sample_location()) == Biome.MONTANE_FOREST


def test_compose_location_structured() -> None:
    structured = compose_location_structured(_sample_location())
    assert structured["location_id"] == "north-trail"
    assert structured["biome"]["value"] == "montane_forest"
    assert structured["weather"]["wind_speed"]["value"] == "breezy"


def test_compose_location_prose_includes_sections() -> None:
    prose = compose_location_prose(_sample_location())
    assert "Location: north-trail" in prose
    assert "Biome:" in prose
    assert "Humidity:" in prose
    assert "Elevation:" in prose


def test_compose_location_yaml() -> None:
    yaml_text = compose_location_yaml(_sample_location())
    assert "location_id: north-trail" in yaml_text
    assert "biome:" in yaml_text
    assert "weather:" in yaml_text
