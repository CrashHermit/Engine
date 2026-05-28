from dataclasses import dataclass, field


@dataclass
class EntityData:
    name: str
    description: str
    scene_position: str


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
