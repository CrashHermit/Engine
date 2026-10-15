"""Configuration for geology generation stages."""

from dataclasses import dataclass, field
from typing import Literal

from src.worldgen.field.priority import PriorityFloodConfig


GrowthMethod = Literal["priority-flood", "dijkstra"]


@dataclass(frozen=True, slots=True)
class MagmaConfig:
    octaves: int = 5
    base_frequency: float = 0.3
    lacunarity: float = 3.0
    persistence: float = 0.5
    descending: bool = True


@dataclass(frozen=True, slots=True)
class PlateConfig:
    plate_count: int = 15
    min_seed_distance: float = 0.1
    irregularity_strength: float = 1.0
    growth_method: GrowthMethod = "priority-flood"
    flood: PriorityFloodConfig = field(default_factory=PriorityFloodConfig)


@dataclass(frozen=True, slots=True)
class CrustConfig:
    continental_seeds: int = 4
    oceanic_seeds: int = 11
    min_seed_distance: float = 0.1
    irregularity_strength: float = 1.0
    octaves: int = 3
    base_frequency: float = 1.0
    lacunarity: float = 2.0
    persistence: float = 0.35
    growth_method: GrowthMethod = "priority-flood"
    flood: PriorityFloodConfig = field(default_factory=PriorityFloodConfig)


@dataclass(frozen=True, slots=True)
class GeologyConfig:
    magma: MagmaConfig = field(default_factory=MagmaConfig)
    plates: PlateConfig = field(default_factory=PlateConfig)
    crust: CrustConfig = field(default_factory=CrustConfig)
