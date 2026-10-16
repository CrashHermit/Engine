"""Configuration for geology generation stages."""

from dataclasses import dataclass, field
from typing import Literal

from src.worldgen.field.priority import PriorityFloodConfig


GrowthMethod = Literal["priority-flood", "dijkstra"]


@dataclass(frozen=True, slots=True)
class CrustDensityConfig:
    continental_base: float = 1.0
    oceanic_base: float = 2.0
    variation_strength: float = 0.2
    noise_frequency: float = 1.0


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
    min_angular_speed: float = 0.05
    max_angular_speed: float = 0.20
    motion_scale: float = 1.0
    growth_method: GrowthMethod = "priority-flood"
    flood: PriorityFloodConfig = field(default_factory=PriorityFloodConfig)


@dataclass(frozen=True, slots=True)
class CrustConfig:
    continental_seeds: int = 18
    oceanic_seeds: int = 33
    min_seed_distance: float = 0.1
    irregularity_strength: float = 1.0
    octaves: int = 3
    base_frequency: float = 1.0
    lacunarity: float = 2.0
    persistence: float = 0.35
    growth_method: GrowthMethod = "priority-flood"
    flood: PriorityFloodConfig = field(default_factory=PriorityFloodConfig)
    density: CrustDensityConfig = field(default_factory=CrustDensityConfig)


@dataclass(frozen=True, slots=True)
class GeologyConfig:
    magma: MagmaConfig = field(default_factory=MagmaConfig)
    plates: PlateConfig = field(default_factory=PlateConfig)
    crust: CrustConfig = field(default_factory=CrustConfig)
