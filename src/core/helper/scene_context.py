from __future__ import annotations

from enum import Enum
from typing import Any

import yaml

from src.core.helper.enum_text import describe, labeled
from src.core.model.biome import BIOME, BIOME_MATRIX, Biome
from src.core.model.climate import (
    GLOBAL_PRECIPITATION,
    TEMPERATURE,
    ClimateData,
)
from src.core.model.environment import EnvironmentData
from src.core.model.location import LocationData
from src.core.model.terrain import (
    DEPTH,
    ELEVATION,
    HYDROLOGY,
    SHORE_HYDROLOGY,
    WATER_DEPTH,
    Hydrology,
    TerrainData,
)
from src.core.model.weather import (
    HUMIDITY,
    PRECIPITATION,
    WIND_DIRECTION,
    WIND_SPEED,
    WeatherData,
)


class SceneContextHelper:
    @staticmethod
    def _entry(member: Enum, descriptions: dict[Enum, str]) -> dict[str, str]:
        return {
            "value": member.name.lower(),
            "description": describe(member, descriptions),
        }

    def resolve_location_biome(self, location: LocationData) -> Biome:
        return BIOME_MATRIX.resolve(location.environment)

    def format_climate(self, climate: ClimateData) -> str:
        return "\n".join(
            [
                f"Temperature: {labeled(climate.temperature, TEMPERATURE)}",
                f"Precipitation: {labeled(climate.precipitation, GLOBAL_PRECIPITATION)}",
            ]
        )

    def format_weather(self, weather: WeatherData) -> str:
        return "\n".join(
            [
                f"Humidity: {labeled(weather.humidity, HUMIDITY)}",
                f"Precipitation: {labeled(weather.precipitation, PRECIPITATION)}",
                (
                    "Wind: "
                    f"{labeled(weather.wind_speed, WIND_SPEED)}; "
                    f"{labeled(weather.wind_direction, WIND_DIRECTION)}"
                ),
            ]
        )

    def format_terrain(self, terrain: TerrainData) -> str:
        lines = [f"Elevation: {labeled(terrain.elevation, ELEVATION)}"]
        if terrain.depth is not None:
            lines.append(f"Underground: {labeled(terrain.depth, DEPTH)}")
        if terrain.hydrology != Hydrology.NONE:
            lines.append(f"Hydrology: {labeled(terrain.hydrology, HYDROLOGY)}")
            if terrain.hydrology not in SHORE_HYDROLOGY:
                lines.append(f"Depth: {labeled(terrain.water_depth, WATER_DEPTH)}")
        return "\n".join(lines)

    def format_biome(self, biome: Biome) -> str:
        return labeled(biome, BIOME)

    def compose_environment_structured(
        self, environment: EnvironmentData
    ) -> dict[str, Any]:
        terrain = environment.terrain
        climate = environment.climate
        return {
            "climate": {
                "temperature": self._entry(climate.temperature, TEMPERATURE),
                "precipitation": self._entry(
                    climate.precipitation, GLOBAL_PRECIPITATION
                ),
            },
            "terrain": {
                "elevation": self._entry(terrain.elevation, ELEVATION),
                "hydrology": self._entry(terrain.hydrology, HYDROLOGY),
                "water_depth": self._entry(terrain.water_depth, WATER_DEPTH),
            },
        }

    def compose_weather_structured(self, weather: WeatherData) -> dict[str, Any]:
        return {
            "humidity": self._entry(weather.humidity, HUMIDITY),
            "precipitation": self._entry(weather.precipitation, PRECIPITATION),
            "wind_speed": self._entry(weather.wind_speed, WIND_SPEED),
            "wind_direction": self._entry(weather.wind_direction, WIND_DIRECTION),
        }

    def compose_location_structured(self, location: LocationData) -> dict[str, Any]:
        biome = self.resolve_location_biome(location)
        return {
            "location_id": location.id,
            "biome": self._entry(biome, BIOME),
            "environment": self.compose_environment_structured(location.environment),
            "weather": self.compose_weather_structured(location.weather),
        }

    def compose_location_prose(self, location: LocationData) -> str:
        biome = self.resolve_location_biome(location)
        sections = [
            f"Location: {location.id}",
            f"Biome: {self.format_biome(biome)}",
            self.format_climate(location.environment.climate),
            self.format_terrain(location.environment.terrain),
            self.format_weather(location.weather),
        ]
        return "\n".join(sections)

    def compose_location_yaml(self, location: LocationData) -> str:
        return yaml.dump(
            self.compose_location_structured(location),
            default_flow_style=False,
            sort_keys=False,
        )
