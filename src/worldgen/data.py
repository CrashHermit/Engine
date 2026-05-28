from dataclasses import dataclass, field


@dataclass
class TileData:
    row: int
    col: int
    neighbors: list[tuple[int, int]] = field(default_factory=list)


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
