from __future__ import annotations

from random import random

from core.model.climate.location import LocationData
from core.model.temperature import Temperature
from core.model.weather.precipitation import Precipitation
from core.model.weather.wind_direction import WindDirectionEnum
from core.model.weather.wind_intensity import WindIntensityEnum


class SceneContextHelper:
    def __init__(self):
        pass

    def generate_temperature_scene_context(self, location_data: LocationData) -> str:
        """
        Generate a scene context for the temperature.

        Args:
            location_data: The location data.

        Returns:
            A string describing the temperature.
        """
        temperature: Temperature = location_data.temperature

        frigid_descriptions = [
            "The air is freezing.",
            "The air is cold.",
            "The air is cool.",
        ]
        freezing_descriptions = [
            "The air is freezing.",
            "The air is cold.",
            "The air is cool.",
        ]
        cool_descriptions = ["The air is cool.", "The air is warm.", "The air is hot."]
        mild_descriptions = ["The air is mild.", "The air is warm.", "The air is hot."]
        warm_descriptions = [
            "The air is warm.",
            "The air is hot.",
            "The air is scorching.",
        ]
        hot_descriptions = [
            "The air is hot.",
            "The air is scorching.",
            "The air is scorching.",
        ]
        scorching_descriptions = [
            "The air is scorching.",
            "The air is scorching.",
            "The air is scorching.",
        ]

        temperature_descriptions: dict[Temperature, list[str]] = {
            Temperature.FRIGID: frigid_descriptions,
            Temperature.FREEZING: freezing_descriptions,
            Temperature.COOL: cool_descriptions,
            Temperature.MILD: mild_descriptions,
            Temperature.WARM: warm_descriptions,
            Temperature.HOT: hot_descriptions,
            Temperature.SCORCHING: scorching_descriptions,
        }

        temperature_description: list[str] = temperature_descriptions[temperature]

        return f"{random.choice(temperature_description)}."

    def generate_precipitation_scene_context(self, location_data: LocationData) -> str:
        """
        Generate a scene context for the precipitation.

        Args:
            location_data: The location data.

        Returns:
            A string describing the precipitation.
        """
        precipitation: Precipitation = location_data.precipitation

        none_descriptions = [
            "There is no precipitation.",
            "The sky is clear.",
            "Nothing is falling from the sky.",
        ]
        drizzle_descriptions = [
            "There is a light drizzle.",
            "There is a light drizzle.",
            "There is a light drizzle.",
        ]
        light_descriptions = [
            "There is a light rain.",
            "There is a light rain.",
            "There is a light rain.",
        ]
        steady_descriptions = [
            "There is a steady rain.",
            "There is a steady rain.",
            "There is a steady rain.",
        ]
        heavy_descriptions = [
            "There is a heavy rain.",
            "There is a heavy rain.",
            "There is a heavy rain.",
        ]
        torrential_descriptions = [
            "There is a torrential rain.",
            "There is a torrential rain.",
            "There is a torrential rain.",
        ]
        cloudburst_descriptions = [
            "There is a cloudburst.",
            "There is a cloudburst.",
            "There is a cloudburst.",
        ]

        precipitation_descriptions: dict[Precipitation, list[str]] = {
            Precipitation.NONE: none_descriptions,
            Precipitation.DRIZZLE: drizzle_descriptions,
            Precipitation.LIGHT: light_descriptions,
            Precipitation.STEADY: steady_descriptions,
            Precipitation.HEAVY: heavy_descriptions,
            Precipitation.TORRENTIAL: torrential_descriptions,
            Precipitation.CLOUDBURST: cloudburst_descriptions,
        }

        precipitation_description: list[str] = precipitation_descriptions[precipitation]

        return f"{random.choice(precipitation_description)}."

    def generate_wind_direction_scene_context(self, location_data: LocationData) -> str:
        """
        Generate a scene context for the wind direction.

        Args:
            location_data: The location data.

        Returns:
            A string describing the wind direction.
        """
        wind_direction: WindDirectionEnum = location_data.wind_direction
        return f"The wind direction is {wind_direction}."
        wind_intensity: WindIntensityEnum = location_data.wind_intensity

        calm_descriptions = [
            "The air is still.",
            "A gentle wind stirs the air.",
            "A steady breeze tugs at clothes and loose leaves.",
        ]
        gentle_descriptions = [
            "A gentle wind stirs the air.",
            "A steady breeze tugs at clothes and loose leaves.",
            "Gusts come and go, whipping dust and branches.",
        ]
        breezy_descriptions = [
            "A steady breeze tugs at clothes and loose leaves.",
            "Gusts come and go, whipping dust and branches.",
            "Strong winds howl; keeping your footing takes effort.",
        ]
        blustery_descriptions = [
            "Gusts come and go, whipping dust and branches.",
            "Strong winds howl; keeping your footing takes effort",
            "The wind screams in violent gusts",
        ]
        gale_descriptions = [
            "Strong winds howl; keeping your footing takes effort.",
            "The wind screams in violent gusts.",
            "The wind is devastating; nothing exposed stands easy.",
        ]
        storm_descriptions = [
            "The wind screams in violent gusts.",
            "The wind is devastating; nothing exposed stands easy.",
            "The wind is devastating; nothing exposed stands easy.",
        ]
        hurricane_descriptions = [
            "The wind is devastating; nothing exposed stands easy.",
            "The wind is devastating; nothing exposed stands easy.",
            "The wind is devastating; nothing exposed stands easy.",
        ]

        wind_intensity_descriptions: dict[WindIntensityEnum, list[str]] = {
            WindIntensityEnum.CALM: calm_descriptions,
            WindIntensityEnum.GENTLE: gentle_descriptions,
            WindIntensityEnum.BREEZY: breezy_descriptions,
            WindIntensityEnum.BLUSTERY: blustery_descriptions,
            WindIntensityEnum.GALE: gale_descriptions,
            WindIntensityEnum.STORM: storm_descriptions,
            WindIntensityEnum.HURRICANE: hurricane_descriptions,
        }

        wind_intensity_description: list[str] = wind_intensity_descriptions[
            wind_intensity
        ]
        return f"{random.choice(wind_intensity_description)}."
