from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Mesh
# ---------------------------------------------------------------------------


@dataclass
class MeshConfig:
    """Parameters for the Voronoi mesh that underpins all simulation layers."""

    cell_count: int = 12000
    lloyd_iterations: int = 2
    width: float = 0.0  # 0 → use float(world_size)
    height: float = 0.0  # 0 → use float(world_size)


# ---------------------------------------------------------------------------
# Elevation
# ---------------------------------------------------------------------------


@dataclass
class NoiseLayerConfig:
    """One spectral band in the layered elevation system.

    Attributes:
        frequency: Circle radius used for the 4D torus mapping; controls
            spatial scale of features.  Low values = large continents,
            high values = small islands.
        weight: Relative contribution of this layer to the combined field
            (weights are normalised before summing).
        octaves: Number of FBm octave summations.
        kind: ``"fbm"`` (default), ``"ridged"``, or ``"billow"``.
    """

    frequency: float
    weight: float
    octaves: int = 4
    kind: str = "fbm"


def _default_three_bands() -> list[NoiseLayerConfig]:
    return [
        NoiseLayerConfig(frequency=0.22, weight=0.50, octaves=4, kind="fbm"),
        NoiseLayerConfig(frequency=0.80, weight=0.35, octaves=4, kind="fbm"),
        NoiseLayerConfig(frequency=2.00, weight=0.15, octaves=3, kind="fbm"),
    ]


@dataclass
class ElevationConfig:
    """Controls how the base elevation field is generated.

    Attributes:
        provider: Which ``ElevationProvider`` to use.
            ``"layered_noise"`` (default) – emergent N-band FBm.
            ``"anchors"`` – directed continent seeds.
        layers: Band list for the ``"layered_noise"`` provider.
        warp_amplitude: Domain-warp displacement strength.
        warp_frequency: Frequency of the domain-warp noise.
        redistribution_power: Exponent applied after normalisation;
            values > 1 push ocean lower and peaks higher.
        elevation_scale: Final multiplier on the remapped height values.
    """

    provider: str = "layered_noise"
    layers: list[NoiseLayerConfig] = field(default_factory=_default_three_bands)
    warp_amplitude: float = 0.18
    warp_frequency: float = 0.5
    redistribution_power: float = 1.35
    elevation_scale: float = 1.0


# ---------------------------------------------------------------------------
# Sea level
# ---------------------------------------------------------------------------


@dataclass
class SeaLevelConfig:
    """Percentile cut that converts raw elevation to ``is_land``."""

    target_land_fraction: float = 0.32


# ---------------------------------------------------------------------------
# Erosion (optional post-sea-level pass)
# ---------------------------------------------------------------------------


@dataclass
class ErosionConfig:
    """Optional stream-power and thermal erosion applied on the mesh."""

    enabled: bool = False
    iterations: int = 3
    stream_power: float = 0.30
    thermal_talus: float = 0.05


# ---------------------------------------------------------------------------
# Landmass labeling
# ---------------------------------------------------------------------------


@dataclass
class LandmassConfig:
    """Size thresholds for classifying connected land components."""

    island_min_fraction: float = 0.005
    landmass_min_fraction: float = 0.08


# ---------------------------------------------------------------------------
# Hydrology
# ---------------------------------------------------------------------------


@dataclass
class HydrologyConfig:
    """River routing and rasterisation parameters."""

    river_flux_threshold: float = 3.0
    river_min_width: float = 1.0
    river_width_scale: float = 0.25
    river_max_width: float = 4.0


# ---------------------------------------------------------------------------
# Climate
# ---------------------------------------------------------------------------


@dataclass
class ClimateConfig:
    """Temperature, precipitation, and wind field parameters."""

    warp_amplitude: float = 8.0
    lapse_rate: float = 1.0
    orographic_multiplier: float = 3.0
    precip_latitude_bands: float = 2.5
    band_weight: float = 0.5
    temperature_bands: float = 1.0
    moisture_advection: float = 0.3
    noise_scale: float = 2.0
    wind_turbulence: float = 0.7
    wind_noise_scale_factor: float = 0.5


# ---------------------------------------------------------------------------
# Biomes
# ---------------------------------------------------------------------------


@dataclass
class BiomeConfig:
    """Biome soft-assignment parameters."""

    blend_sharpness: float = 2.0
    weight_cutoff: float = 0.05


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------


@dataclass
class WorldgenConfig:
    """Top-level config for the entire worldgen pipeline."""

    seed: int = 0
    size: int = 100
    mesh: MeshConfig = field(default_factory=MeshConfig)
    elevation: ElevationConfig = field(default_factory=ElevationConfig)
    sea_level: SeaLevelConfig = field(default_factory=SeaLevelConfig)
    erosion: ErosionConfig = field(default_factory=ErosionConfig)
    landmass: LandmassConfig = field(default_factory=LandmassConfig)
    hydrology: HydrologyConfig = field(default_factory=HydrologyConfig)
    climate: ClimateConfig = field(default_factory=ClimateConfig)
    biome: BiomeConfig = field(default_factory=BiomeConfig)
