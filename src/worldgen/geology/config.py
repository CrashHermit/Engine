"""Configuration for geology generation stages."""

from dataclasses import dataclass, field
from typing import Literal

from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.priority import PriorityFloodConfig


GrowthMethod = Literal["priority-flood", "dijkstra"]


@dataclass(frozen=True, slots=True)
class CrustDensityConfig:
    continental_base: float = 1.0
    oceanic_base: float = 2.0
    variation_strength: float = 0.2
    noise_frequency: float = 1.0


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
    field: NoiseConfig = field(default_factory=NoiseConfig)


@dataclass(frozen=True, slots=True)
class PlateMotionConfig:
    min_angular_speed: float = 0.0
    max_angular_speed: float = 1.0


@dataclass(frozen=True, slots=True)
class CrustConfig:
    continental_seeds: int = 10
    oceanic_seeds: int = 33
    min_seed_distance: float = 0.1
    irregularity_strength: float = 1.0
    growth_method: GrowthMethod = "priority-flood"
    flood: PriorityFloodConfig = field(default_factory=PriorityFloodConfig)
    density: CrustDensityConfig = field(default_factory=CrustDensityConfig)
    field: NoiseConfig = field(
        default_factory=lambda: NoiseConfig(
            octaves=3,
            base_frequency=1.0,
            lacunarity=2.0,
            persistence=0.35,
        )
    )


@dataclass(frozen=True, slots=True)
class HotspotConfig:
    count: int = 12
    min_seed_distance: float = 0.3
    boundary_clearance_percent: float = 1.25
    potential: NoiseConfig = field(default_factory=NoiseConfig)
    potential_bias: float = 4.0
    min_width_percent: float = 0.5
    max_width_percent: float = 1.0
    min_height_percent: float = 0.03
    max_height_percent: float = 0.1


@dataclass(frozen=True, slots=True)
class VolcanismConfig:
    supplied_site_count: int = 24
    historical_extinct_site_count: int = 8
    min_site_distance: float = 0.12
    eruption_probability: float = 0.08
    potential_threshold: float = 0.18
    supply_persistence_probability: float = 0.75
    min_historical_width_percent: float = 0.35
    max_historical_width_percent: float = 0.9
    min_historical_height_percent: float = 0.02
    max_historical_height_percent: float = 0.08


@dataclass(frozen=True, slots=True)
class GeologyConfig:
    plates: PlateConfig = field(default_factory=PlateConfig)
    crust: CrustConfig = field(default_factory=CrustConfig)
    hotspots: HotspotConfig = field(default_factory=HotspotConfig)
    volcanism: VolcanismConfig = field(default_factory=VolcanismConfig)
