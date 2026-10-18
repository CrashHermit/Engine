"""Spherical elevation profiles and relief settings."""

from dataclasses import dataclass, field

from src.worldgen.field.noise import NoiseConfig


@dataclass(frozen=True, slots=True)
class CoastalWidthConfig:
    base_percent: float
    variation_strength: float = 0.3
    noise_frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class CollisionConfig:
    width_percent: float = 2.5
    height_percent: float = 0.16
    crest_width_fraction: float = 0.3
    crest_height_multiplier: float = 2.0


@dataclass(frozen=True, slots=True)
class SubductionConfig:
    width_percent: float = 2.5
    height_percent: float = 0.15
    trench_depth_multiplier: float = 2.25
    trench_width_fraction: float = 0.2
    arc_offset_fraction: float = 0.25
    arc_width_fraction: float = 0.2
    arc_height_multiplier: float = 1.5
    arc_variation_strength: float = 0.6
    arc_noise_frequency: float = 6.0


@dataclass(frozen=True, slots=True)
class DivergenceConfig:
    width_percent: float = 1.0
    height_percent: float = 0.075
    axial_width_fraction: float = 0.25
    axial_depth_multiplier: float = 0.65
    shoulder_height_multiplier: float = 0.35


@dataclass(frozen=True, slots=True)
class TransformConfig:
    width_percent: float = 0.75
    height_percent: float = 0.05


@dataclass(frozen=True, slots=True)
class DeformationConfig:
    collision: CollisionConfig = field(default_factory=CollisionConfig)
    subduction: SubductionConfig = field(default_factory=SubductionConfig)
    divergence: DivergenceConfig = field(default_factory=DivergenceConfig)
    transform: TransformConfig = field(default_factory=TransformConfig)


@dataclass(frozen=True, slots=True)
class BuoyancyConfig:
    """Elevation response to relative crust-density anomalies."""

    continental_height_percent: float = 0.02
    oceanic_height_percent: float = 0.04


@dataclass(frozen=True, slots=True)
class CoastalConfig:
    """Widths as percentages of circumference; heights as percentages of radius."""

    inland: CoastalWidthConfig = field(
        default_factory=lambda: CoastalWidthConfig(base_percent=2.0)
    )
    shelf: CoastalWidthConfig = field(
        default_factory=lambda: CoastalWidthConfig(base_percent=1.25)
    )
    slope: CoastalWidthConfig = field(
        default_factory=lambda: CoastalWidthConfig(base_percent=1.25)
    )
    interior_height_percent: float = 0.00942
    shelf_depth_percent: float = 0.00314
    basin_depth_percent: float = 0.08063
    buoyancy: BuoyancyConfig = field(default_factory=BuoyancyConfig)


@dataclass(frozen=True, slots=True)
class TerrainVariationConfig:
    amplitude_percent: float = 0.0215
    noise: NoiseConfig = field(
        default_factory=lambda: NoiseConfig(
            octaves=4,
            base_frequency=4.0,
            lacunarity=2.0,
            persistence=0.5,
        )
    )


@dataclass(frozen=True, slots=True)
class ImpactConfig:
    """Continuous meteor-impact source settings."""

    count: int = 40
    min_radius_percent: float = 0.15
    max_radius_percent: float = 4.0
    min_depth_percent: float = 0.005
    max_depth_percent: float = 0.14
    min_sharpness: float = 1.0
    max_sharpness: float = 8.0
    rim_height_fraction: float = 0.25
    ejecta_width_fraction: float = 1.0


@dataclass(frozen=True, slots=True)
class ElevationConfig:
    """Coastal, tectonic, impact, and broad terrain-height settings."""

    coastal: CoastalConfig = field(default_factory=CoastalConfig)
    deformation: DeformationConfig = field(default_factory=DeformationConfig)
    variation: TerrainVariationConfig = field(default_factory=TerrainVariationConfig)
    impacts: ImpactConfig = field(default_factory=ImpactConfig)
