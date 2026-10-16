"""Top-level configuration for world generation."""

from dataclasses import dataclass, field

from src.worldgen.geology.config import GeologyConfig
from src.worldgen.elevation.config import ElevationConfig


@dataclass(frozen=True, slots=True)
class PlanetConfig:
    radius_m: float = 6_371_000.0


@dataclass(frozen=True, slots=True)
class WorldgenConfig:
    seed: int = 123
    subdivision_frequency: int = 40
    geology: GeologyConfig = field(default_factory=GeologyConfig)
    elevation: ElevationConfig = field(default_factory=ElevationConfig)
    planet: PlanetConfig = field(default_factory=PlanetConfig)
