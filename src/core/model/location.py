from __future__ import annotations

from dataclasses import dataclass, field

from src.core.model.entity import EntityData
from src.core.model.environment import EnvironmentData
from src.core.model.weather import WeatherData


@dataclass
class LocationData:
    id: str
    environment: EnvironmentData
    weather: WeatherData
    


@dataclass
class LocationState:
    location: LocationData
    neighbors: list[LocationData] = field(default_factory=list)
    entities: list[EntityData] = field(default_factory=list)
