from __future__ import annotations

from dataclasses import dataclass, field

from src.core.model.entity import EntityData
from src.core.model.environment import EnvironmentData
from src.core.model.weather import WeatherData


@dataclass
class LocationData:
    id: str
    name: str = ""
    description: str = ""
    environment: EnvironmentData | None = None
    weather: WeatherData | None = None


@dataclass
class LocationState:
    location: LocationData
    environment: EnvironmentData | None = None
    weather: WeatherData | None = None
    neighbors: list[LocationData] = field(default_factory=list)
    entities: list[EntityData] = field(default_factory=list)
