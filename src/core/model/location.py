from __future__ import annotations

from dataclasses import dataclass, field

from src.core.model.entity import EntityData


@dataclass
class LocationData:
    id: str
    name: str
    description: str


@dataclass
class LocationState:
    location: LocationData
    neighbors: list[LocationData] = field(default_factory=list)
    entities: list[EntityData] = field(default_factory=list)
