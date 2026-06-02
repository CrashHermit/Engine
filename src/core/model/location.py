from dataclasses import dataclass, field

from src.core.mechanic.harm import WoundPool
from src.core.model.entity import Danger, EntityKind
from src.core.model.threat import Channel


@dataclass
class EntityData:
    name: str
    description: str
    scene_position: str
    # Creature vs inert prop. Defaults to OBJECT so only entities explicitly
    # tagged as creatures are foes (can be targeted/defeated).
    kind: EntityKind = EntityKind.OBJECT
    # Structural spine fed to the threat classifier + magnitude cap. Defaulted
    # so existing call sites need not change.
    danger: Danger = Danger.STANDARD
    threat_channels: frozenset[Channel] = field(default_factory=frozenset)
    id: str = ""
    # Effect-on-target clock: the player's action fills it; full = defeated.
    # Capacity is set from danger by the service (this default is a placeholder
    # for in-memory construction).
    wound: WoundPool = field(default_factory=WoundPool)


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