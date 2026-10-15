"""Top-level configuration for world generation."""

from dataclasses import dataclass, field

from src.worldgen.geology.config import GeologyConfig
from src.worldgen.terrain.config import TerrainConfig


@dataclass(frozen=True, slots=True)
class PlanetConfig:
    radius_m: float = 6_371_000.0


@dataclass(frozen=True, slots=True)
class WorldgenConfig:
    seed: int = 123
    subdivision_frequency: int = 20
    geology: GeologyConfig = field(default_factory=GeologyConfig)
    terrain: TerrainConfig = field(default_factory=TerrainConfig)
    planet: PlanetConfig = field(default_factory=PlanetConfig)
