from __future__ import annotations

from enum import StrEnum
from typing import Any

from src.core.helper.enum_text import describe, labeled
from src.core.model.biome import BIOME, Biome, biome_from
from src.core.model.climate import (
    GLOBAL_PRECIPITATION,
    TEMPERATURE,
    ClimateData,
)
from src.core.model.environment import EnvironmentData
from src.core.model.location import LocationData
from src.core.model.terrain import (
    ELEVATION,
    SALINITY,
    WATER_DEPTH,
    WATER_FORM,
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
    def __init__(self):
        self.climate: ClimateData = ClimateData()
        self.terrain: TerrainData = TerrainData()
        self.weather: WeatherData = WeatherData()
        self.location: LocationData = LocationData()

    def resolve_location_biome(self) -> Biome:
        return biome_from(
            temperature=self.climate.temperature,
            precipitation=self.climate.precipitation,
            elevation=self.terrain.elevation,
            water_form=self.terrain.water_form,
            salinity=self.terrain.salinity,
            water_depth=self.terrain.water_depth,
            coastal=self.terrain.coastal,
        )
    def _entry(self, member: StrEnum, descriptions: dict[StrEnum, str]) -> dict[str, str]:
        return {
            "value": member.value,
            "description": describe(member, descriptions),
        }


    def resolve_location_biome(self, location: LocationData) -> Biome:
        terrain = location.environment.terrain
        climate = location.environment.climate
        return biome_from(
            temperature=climate.temperature,
            precipitation=climate.precipitation,
            elevation=terrain.elevation,
            water_form=terrain.water_form,
            salinity=terrain.salinity,
            water_depth=terrain.water_depth,
            coastal=terrain.coastal,
        )


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
                f"Humidity: {labeled(weather.humidity.value, HUMIDITY)}",
                f"Precipitation: {labeled(weather.precipitation.value, PRECIPITATION)}",
                (
                    "Wind: "
                    f"{labeled(weather.wind_speed.value, WIND_SPEED)}; "
                    f"{labeled(weather.wind_direction.value, WIND_DIRECTION)}"
                ),
            ]
        )


    def format_terrain(self, terrain: TerrainData) -> str:
        lines = [f"Elevation: {labeled(terrain.elevation, ELEVATION)}"]
        if terrain.water_form.value != "none":
            resolved = terrain.effective_salinity
            lines.extend(
                [
                    f"Water: {labeled(TerrainData.water_form.value, WATER_FORM)}",
                    f"Salinity: {labeled(resolved, SALINITY)}",
                    f"Depth: {labeled(TerrainData.water_depth.value, WATER_DEPTH)}",
                ]
            )
        if terrain.coastal:
            lines.append("Coastal: shore-adjacent land")
        return "\n".join(lines)


    def format_biome(self, biome: Biome) -> str:
        return labeled(biome, BIOME)


    def compose_environment_structured(self, environment: EnvironmentData) -> dict[str, Any]:
        terrain = environment.terrain
        climate = environment.climate
        structured: dict[str, Any] = {
            "climate": {
                ClimateData.temperature.value: self._entry(climate.temperature, TEMPERATURE),
                ClimateData.precipitation.value: self._entry(climate.precipitation, GLOBAL_PRECIPITATION),
            },
            "terrain": {
                TerrainData.elevation.value: self._entry(terrain.elevation, ELEVATION),
                TerrainData.water_form.value: self._entry(terrain.water_form, WATER_FORM),
                TerrainData.water_depth.value: self._entry(terrain.water_depth, WATER_DEPTH),
                "coastal": terrain.coastal,
            },
        }
        if terrain.water_form.value != "none":
            resolved = terrain.effective_salinity
            structured["terrain"]["salinity"] = self._entry(resolved, SALINITY)
        return structured


    def compose_weather_structured(self, weather: WeatherData) -> dict[str, Any]:
        return {
            WeatherData.humidity.value: self._entry(weather.humidity, HUMIDITY),
            WeatherData.precipitation.value: self._entry(weather.precipitation, PRECIPITATION),
            WeatherData.wind_speed.value: self._entry(weather.wind_speed, WIND_SPEED),
            WeatherData.wind_direction.value: self._entry(weather.wind_direction, WIND_DIRECTION),
        }


    def compose_location_structured(location: LocationData) -> dict[str, Any]:
        biome = resolve_location_biome(location)
        return {
            "location_id": location.id,
            "biome": _entry(biome, BIOME),
            "environment": compose_environment_structured(location.environment),
            "weather": compose_weather_structured(location.weather),
        }


    def compose_location_prose(location: LocationData) -> str:
        biome = resolve_location_biome(location)
        sections = [
            f"Location: {location.id}",
            f"Biome: {format_biome(biome)}",
            format_climate(location.environment.climate),
            format_terrain(location.environment.terrain),
            format_weather(location.weather),
        ]
        return "\n".join(sections)
