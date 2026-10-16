"""Coarse spherical elevation and tectonic relief settings."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CoastalWidthConfig:
    base_percent: float
    variation_strength: float = 0.3
    noise_frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class CollisionConfig:
    width_percent: float = 2.5
    height_percent: float = 0.15
    crest_width_fraction: float = 0.3
    crest_height_multiplier: float = 2.0


@dataclass(frozen=True, slots=True)
class SubductionConfig:
    width_percent: float = 2.5
    height_percent: float = 0.15
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
class DeformationConfig:
    collision: CollisionConfig = field(default_factory=CollisionConfig)
    subduction: SubductionConfig = field(default_factory=SubductionConfig)
    divergence: DivergenceConfig = field(default_factory=DivergenceConfig)


@dataclass(frozen=True, slots=True)
class BuoyancyConfig:
    """Elevation response to relative crust-density anomalies."""

    continental_height_percent: float = 0.02
    oceanic_height_percent: float = 0.04


@dataclass(frozen=True, slots=True)
class ElevationConfig:
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
    basin_depth_percent: float = 0.07063
    deformation: DeformationConfig = field(default_factory=DeformationConfig)
    buoyancy: BuoyancyConfig = field(default_factory=BuoyancyConfig)
