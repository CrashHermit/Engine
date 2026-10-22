"""Configuration for continuous geological fields."""

from dataclasses import dataclass, field

from src.worldgen.field.boundary_motion import BoundaryMotionConfig


@dataclass(frozen=True, slots=True)
class PlateMotionConfig:
    """Angular-speed range for independent, isotropic Euler rotations."""

    min_angular_speed: float = 0.0
    max_angular_speed: float = 1.0


@dataclass(frozen=True, slots=True)
class PlateConfig:
    """Continuous tectonic partition and plate-motion settings."""

    plate_count: int = 32
    # Percentage of the unit reference length; the planet maps one unit to radius.
    transition_half_width_percent: float = 12.0
    motion: PlateMotionConfig = field(default_factory=PlateMotionConfig)


@dataclass(frozen=True, slots=True)
class CrustPartitionConfig:
    """Independent continuous crust partition seed counts and transition width."""

    continental_seeds: int = 6
    oceanic_seeds: int = 18
    # Material blend spans remain dimensionless; this is a spatial overlap width.
    transition_half_width_percent: float = 12.0


@dataclass(frozen=True, slots=True)
class MaterialBlendConfig:
    """Continental influence interval that blends geological profile families."""

    midpoint: float = 0.5
    transition_width: float = 0.2


@dataclass(frozen=True, slots=True)
class PolarityConfig:
    """Relative scale and persistent tie bias for overriding-side preference."""

    preference_scale: float = 0.2
    seeded_bias: float = 0.25


@dataclass(frozen=True, slots=True)
class CrustDensityConfig:
    """Relative procedural density-anomaly settings."""

    variation_strength: float = 0.2
    noise_frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class GeologyConfig:
    """Configuration for independent plate and crust fields."""

    boundary_motion: BoundaryMotionConfig = field(default_factory=BoundaryMotionConfig)
    plates: PlateConfig = field(default_factory=PlateConfig)
    crust: CrustPartitionConfig = field(default_factory=CrustPartitionConfig)
    material_blend: MaterialBlendConfig = field(default_factory=MaterialBlendConfig)
    polarity: PolarityConfig = field(default_factory=PolarityConfig)
    density: CrustDensityConfig = field(default_factory=CrustDensityConfig)
