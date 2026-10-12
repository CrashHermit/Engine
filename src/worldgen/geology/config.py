"""Configuration for the procedural geology stage."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeologyConfig:
    octaves: int = 5
    base_frequency: float = 0.3
    lacunarity: float = 3.0
    persistence: float = 0.5
    plate_count: int = 15
    min_seed_distance: float = 0.1
    descending: bool = True
