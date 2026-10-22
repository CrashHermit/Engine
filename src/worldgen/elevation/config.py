"""Configuration for source elevation profiles and world-space variation."""

from dataclasses import dataclass, field

from src.worldgen.elevation.volcanism import VolcanismConfig
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.elevation.ridge_detail import RidgeDetailConfig


REFERENCE_RADIUS_M = 6_371_000.0


@dataclass(frozen=True, slots=True)
class SourceCoastalSpanConfig:
    """Dimensionless coastal span and independent procedural modulation."""

    span: float
    variation_strength: float = 0.3
    noise_frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class SourceCoastalConfig:
    """Coastal relief heights and density responses as percentages of radius."""

    coastline_weight: float = 0.65
    inland: SourceCoastalSpanConfig = field(
        default_factory=lambda: SourceCoastalSpanConfig(0.2)
    )
    shelf: SourceCoastalSpanConfig = field(
        default_factory=lambda: SourceCoastalSpanConfig(0.15)
    )
    slope: SourceCoastalSpanConfig = field(
        default_factory=lambda: SourceCoastalSpanConfig(0.25)
    )
    interior_height_percent: float = 0.0094
    shelf_depth_percent: float = 0.0031
    # About 4 km at the reference radius; separate from trench relief.
    basin_depth_percent: float = 0.0628
    continental_buoyancy_percent: float = 0.0157
    oceanic_buoyancy_percent: float = 0.0314


@dataclass(frozen=True, slots=True)
class SourceReliefConfig:
    """Tectonic profile width and relief height as percentages of radius."""

    width_percent: float = 12.0
    height_percent: float = 0.0392

    @property
    def width_fraction(self) -> float:
        """Return source-space width as a fraction of unit-sphere radius."""
        return self.width_percent / 100.0

    @property
    def height_fraction(self) -> float:
        """Return relief height as a fraction of unit-sphere radius."""
        return self.height_percent / 100.0


@dataclass(frozen=True, slots=True)
class TectonicResponseConfig:
    """Tectonic spatial/height percentages and independent motion-response smoothing."""

    # Preserve narrow features while spreading the broad collision/ridge flanks.
    collision_crest_width_fraction: float = 0.2
    ridge_axial_width_fraction: float = 0.125
    # Calibrated independently of trench depth at Earth-reference scale.
    subduction_arc_height_multiplier: float = 1.05
    # Scales the trench independently from convergence and arc uplift.
    subduction_trench_depth_multiplier: float = 0.5
    # Positive regularization scale in motion units, not a spatial percentage.
    motion_smoothing_width: float = 0.01

    collision: SourceReliefConfig = field(
        default_factory=lambda: SourceReliefConfig(
            width_percent=18.0, height_percent=0.03534
        )
    )
    subduction: SourceReliefConfig = field(
        default_factory=lambda: SourceReliefConfig(height_percent=0.0942)
    )
    rift: SourceReliefConfig = field(
        default_factory=lambda: SourceReliefConfig(height_percent=0.0314)
    )
    ridge: SourceReliefConfig = field(
        default_factory=lambda: SourceReliefConfig(
            width_percent=24.0, height_percent=0.03534
        )
    )
    transform: SourceReliefConfig = field(
        default_factory=lambda: SourceReliefConfig(
            width_percent=3.6, height_percent=0.00785
        )
    )
    shear: SourceReliefConfig = field(
        default_factory=lambda: SourceReliefConfig(
            width_percent=3.6, height_percent=0.00392
        )
    )


@dataclass(frozen=True, slots=True)
class TerrainVariationConfig:
    """Noise amplitude as a percentage of planetary radius."""

    amplitude_percent: float = 0.0047
    noise: NoiseConfig = field(
        default_factory=lambda: NoiseConfig(
            octaves=4,
            base_frequency=4.0,
            lacunarity=2.0,
            persistence=0.5,
        )
    )


@dataclass(frozen=True, slots=True)
class ElevationConfig:
    """Source coastal/tectonic profiles and final world-space variation."""

    coastal: SourceCoastalConfig = field(default_factory=SourceCoastalConfig)
    tectonic: TectonicResponseConfig = field(default_factory=TectonicResponseConfig)
    variation: TerrainVariationConfig = field(default_factory=TerrainVariationConfig)
    volcanism: VolcanismConfig = field(default_factory=VolcanismConfig)
    ridge_detail: RidgeDetailConfig = field(default_factory=RidgeDetailConfig)
