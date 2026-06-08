from __future__ import annotations

from dataclasses import dataclass, field
from src.core.model.environment.climate.biome import BiomeEnum

@dataclass
class BiomeWeights:
    biome: BiomeEnum
    weight: float

@dataclass
class GridPositionData:
    x: int = 0
    y: int = 0
    z: float = 0.0
    temperature: float = 0.0
    precipitation: float = 0.0
    wind_u: float = 0.0
    wind_v: float = 0.0
    wind_magnitude: float = 0.0
    river_volume: float = 0.0  # Tracks accumulated water flow
    is_lake: bool = False      # Flags if water gets trapped
    biome_weights: list[BiomeWeights] = field(default_factory=list)


@dataclass
class GridTileData:
    position: GridPositionData = GridPositionData()
    neighbors: list[GridPositionData] = field(default_factory=list)

@dataclass
class WorldData:
    size: int = 100
    seed: int = 0
    noise_scale: float = 1.0
    roughness: float = 1.0
    grid: list[GridTileData] = field(default_factory=list)