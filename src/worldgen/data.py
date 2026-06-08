from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

@dataclass
class GridPositionData:
    x: int
    y: int
    z: float
    temperature: float
    precipitation: float


@dataclass
class GridTileData:
    position: GridPositionData
    neighbors: list[GridPositionData] = field(default_factory=list)

@dataclass
class WorldData:
    size: int
    seed: int
    noise_scale: float
    roughness: float
    grid: list[GridTileData] = field(default_factory=list)