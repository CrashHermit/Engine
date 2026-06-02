from dataclasses import dataclass, field


@dataclass
class TileData:
    row: int
    col: int
    neighbors: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class EntityGen:
    name: str
    description: str
    scene_position: str
    danger: str = "standard"
    threat_channels: str = ""


@dataclass
class LocationGen:
    name: str
    description: str
    is_center: bool = False
    entities: list[EntityGen] = field(default_factory=list)


@dataclass
class DungeonData:
    # Locations and the adjacency pairs (indices into `locations`) that connect them.
    locations: list[LocationGen] = field(default_factory=list)
    connections: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class WorldData:
    name: str
    description: str
    seed: int
    size: int
    biome: str
    temperature: float
    precipitation: float
    elevation: float
    tiles: dict[tuple[int, int], TileData] = field(default_factory=dict)
    dungeon: DungeonData | None = None
