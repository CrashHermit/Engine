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
    major_count: int
    major_radius_pct: int
    detail_count: int
    detail_radius_pct: int
    tiles: dict[tuple[int, int], TileData] = field(default_factory=dict)
