from dataclasses import dataclass, field

from src.core.model.entity import Danger
from src.core.model.threat import Channel


@dataclass
class EntityData:
    name: str
    description: str
    scene_position: str
    # Structural spine fed to the threat classifier + magnitude cap. Defaulted
    # so existing call sites need not change.
    danger: Danger = Danger.STANDARD
    threat_channels: frozenset[Channel] = field(default_factory=frozenset)
    id: str = ""


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