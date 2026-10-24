"""Configuration for continuous geological fields."""

from dataclasses import dataclass, field

from src.worldgen.field.boundary_motion import BoundaryMotionConfig
from src.worldgen.geology.crust_field import CrustPartitionConfig
from src.worldgen.geology.crust_influence import MaterialBlendConfig
from src.worldgen.geology.density import CrustDensityConfig
from src.worldgen.geology.plate_config import PlateConfig
from src.worldgen.geology.subduction_preference import PolarityConfig


@dataclass(frozen=True, slots=True)
class GeologyConfig:
    """Configuration for independent plate and crust fields."""

    boundary_motion: BoundaryMotionConfig = field(default_factory=BoundaryMotionConfig)
    plates: PlateConfig = field(default_factory=PlateConfig)
    crust: CrustPartitionConfig = field(default_factory=CrustPartitionConfig)
    material_blend: MaterialBlendConfig = field(default_factory=MaterialBlendConfig)
    polarity: PolarityConfig = field(default_factory=PolarityConfig)
    density: CrustDensityConfig = field(default_factory=CrustDensityConfig)
