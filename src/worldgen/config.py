"""Top-level configuration for continuous world generation."""

from dataclasses import dataclass, field

from src.worldgen.elevation.config import ElevationConfig
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.warp import ShearWarpConfig
from src.worldgen.geology.config import GeologyConfig
from src.worldgen.surface.config import SurfaceConfig


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
    surface: SurfaceConfig = field(default_factory=SurfaceConfig)
    warp: ShearWarpConfig = field(
        default_factory=lambda: ShearWarpConfig(
            iterations=4, amplitude=0.24, lacunarity=1.7, gain=0.65
        )
    )
    warp_noise: NoiseConfig = field(
        default_factory=lambda: NoiseConfig(
            octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5
        )
    )
