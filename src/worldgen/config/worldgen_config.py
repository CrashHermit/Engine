from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Mesh
# ---------------------------------------------------------------------------


@dataclass
class MeshConfig:
    """Parameters for the Voronoi mesh that underpins all simulation layers."""

    cell_count: int = 12000  # Target number of Voronoi cells (sites)
    lloyd_iterations: int = 2  # Lloyd relaxation passes for more uniform cell sizes
    width: float = 0.0  # Torus width in world units; 0 uses float(world size)
    height: float = 0.0  # Torus height in world units; 0 uses float(world size)


# ---------------------------------------------------------------------------
# Plates
# ---------------------------------------------------------------------------


@dataclass
class PlatesConfig:
    """Tectonic plate partitioning and boundary uplift."""

    n_plates: int = 12  # Number of seed plates grown across the mesh
    growth_raggedness: float = (
        2.0  # Random cost added to heap priority for organic borders; 0 = round blobs
    )
    continental_fraction: float = (
        0.45  # Probability each plate is continental vs oceanic
    )
    continental_uplift: float = 1.0  # Base uplift rate assigned to continental plates
    oceanic_uplift: float = 0.0  # Base uplift rate assigned to oceanic plates
    belt_width: int = (
        4  # BFS hops to smear boundary collision/rift intensity into mountain belts
    )
    belt_strength: float = 0.8  # Multiplier on convergent (collision) boundary uplift
    belt_falloff: float = 0.6  # intensity multiplier per BFS hop
    rift_strength: float = (
        0.3  # Multiplier on divergent (rift) boundary uplift reduction
    )
    belt_noise_scale: float = (
        0.5  # Amplitude of noise modulating smeared belt intensity
    )
    uplift_noise_floor: float = (
        0.05  # Minimum fbm noise multiplier so oceanic plates are not perfectly flat
    )


# ---------------------------------------------------------------------------
# Erosion
# ---------------------------------------------------------------------------


@dataclass
class ErosionConfig:
    """Stream-power erosion and hillslope diffusion on the mesh."""

    iterations: int = 50  # Number of flood-route-erode-diffuse passes
    dt: float = (
        0.1  # Implicit solver timestep; stable at large values unlike explicit erosion
    )
    K: float = 0.3  # Stream-power erosion coefficient (higher = more valley carving)
    m: float = 0.5  # Drainage-area exponent in the stream-power law
    diffusion: float = 0.08  # Hillslope relaxation toward neighbour mean per pass
    base_level_fraction: float = (
        0.1  # Lowest elevation percentile treated as provisional ocean for routing
    )
    initial_scale: float = (
        1.0  # Scales uplift when seeding terrain height before the erosion loop
    )
    initial_noise_amplitude: float = (
        0.05  # Small noise added to the initial height field
    )


# ---------------------------------------------------------------------------
# Sea level
# ---------------------------------------------------------------------------


@dataclass
class SeaLevelConfig:
    """Percentile cut that converts raw elevation to is_land."""

    target_land_fraction: float = (
        0.32  # Desired fraction of land cells after sea-level placement
    )
    coast_smoothing_passes: int = (
        2  # Laplacian relaxation passes on elevation before the cut (0 = off)
    )
    coast_smoothing_strength: float = (
        0.5  # Blend toward neighbor mean per smoothing pass, in [0, 1]
    )


# ---------------------------------------------------------------------------
# Landmass labeling
# ---------------------------------------------------------------------------


@dataclass
class LandmassConfig:
    """Size thresholds for classifying connected land components."""

    island_min_fraction: float = (
        0.005  # Minimum land fraction to count as an island (class 1)
    )
    landmass_min_fraction: float = (
        0.08  # Minimum land fraction to count as a major landmass (class 2+)
    )


@dataclass
class InsolationConfig:
    """Authored energy pattern (no latitude on a torus)."""

    bands: int = 1          # Number of hot/cold ring pairs around the torus
    contrast: float = 0.8   # Spread of climate zones; <1 flattens, >1 sharpens
    wobble: float = 0.0     # Low-freq noise warp on the ring lines; 0 = laser-straight

# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------


@dataclass
class TemperatureConfig:
    """Lapse rate and maritime moderation on top of insolation."""

    lapse_rate: float = 0.3         # Cooling per unit land elevation
    maritime_reach: float = 4.0     # Coast-distance decay length for ocean moderation
    maritime_strength: float = 0.4  # How strongly coasts pull toward sea temperature

# ---------------------------------------------------------------------------
# Wind
# ---------------------------------------------------------------------------


@dataclass
class WindConfig:
    """Prevailing wind belts and terrain deflection."""

    belt_count: int = 3                # Zonal belts around the ring
    meridional_strength: float = 0.3   # North-south component amplitude
    turbulence: float = 0.4            # FBm wobble amplitude on each component
    deflection: float = 0.5            # How hard wind bends away from uphill (step 4)

# ---------------------------------------------------------------------------
# Moisture
# ---------------------------------------------------------------------------


@dataclass
class MoistureConfig:
    """Ocean-sourced moisture advected downwind and rained out."""

    passes: int = 30           # Advection iterations
    evaporation: float = 1.0   # Ocean moisture refill scale (x temperature)
    base_rain: float = 0.035   # Fraction rained out per inland step (drying rate)
    oro: float = 0.6           # Orographic (uphill) rainout multiplier
    chill: float = 0.3         # Temperature-drop rainout multiplier
    wet_reference_percentile: float = (
        99.0  # Land-precip percentile mapped to 1.0 (near-max; avoids top-band pile-up)
    )
    precip_gamma: float = (
        0.5  # Wetness curve on normalized precip; <1 lifts dry/mid bands, =1 linear
    )


# ---------------------------------------------------------------------------
# Water (Phase 3)
# ---------------------------------------------------------------------------


@dataclass
class RiverConfig:
    """River extraction and tile rasterization."""

    river_fraction: float = 0.05  # Percentile of land discharge that qualifies as a river
    w_scale: float = 0.3          # Visual width scale factor on the tile grid
    min_w: float = 0.5            # Minimum river width in tiles
    max_w: float = 8.0            # Maximum river width in tiles


@dataclass
class LakeConfig:
    """Lake extraction parameters."""

    epsilon: float = 1e-6  # Minimum depth for a lake cell (avoids noise)


# ---------------------------------------------------------------------------
# Savagery (Phase 4)
# ---------------------------------------------------------------------------


@dataclass
class SavageryConfig:
    """Legible danger as a weighted blend of named geography components."""

    remoteness_weight: float = 0.35   # coast_distance, max-normalized
    harshness_weight: float = 0.30    # climate distance from comfort (0.55, 0.5)
    ruggedness_weight: float = 0.15   # slope, percentile-normalized
    noise_weight: float = 0.20        # FBm surprise
    magic_weight: float = 0.0         # corrupt zones breed savagery (wire after step 5)
    comfort_temperature: float = 0.55  # Most-comfortable temperature (harshness origin)
    comfort_precipitation: float = 0.5  # Most-comfortable precipitation (harshness origin)
    ruggedness_percentile: float = 95.0  # Percentile that normalizes slope to 1.0
    noise_frequency: float = 3.0      # Surprise-noise spatial frequency (relative to span)


# ---------------------------------------------------------------------------
# Leylines (Phase 4)
# ---------------------------------------------------------------------------


@dataclass
class LeylineConfig:
    """Nexus placement, the leyline web, and magic-field rasterization."""

    count: int = 18              # Target number of nexuses to place
    min_spacing: float = 0.18    # Greedy spacing as a fraction of world span
    peak_percentile: float = 90.0  # Elevation percentile that counts as a peak
    peak_bonus: float = 1.0      # Score bonus for peak cells
    lake_outlet_bonus: float = 0.8  # Score bonus for lake-outlet cells
    confluence_bonus: float = 0.9   # Score bonus for river confluences (>=2 inflows)
    ring_bonus: float = 0.5      # Score bonus near the hot/cold ring lines
    score_noise: float = 0.4     # FBm jitter so similar terrain still varies
    edge_k: int = 4              # Candidate edges: each nexus to its k nearest fellows
    extra_loops: int = 3         # Shortest rejected edges added back as loops
    purity: float = 2.0          # Valence sharpening toward the poles (sign*|v|^(1/purity))
    channel_purity: float = 2.0  # Channel-weight sharpening exponent
    line_reach: float = 0.08     # Strength falloff length from a leyline (fraction of span)
    nexus_reach: float = 0.03    # Tighter falloff length of the nexus bump
    nexus_boost: float = 0.6     # Extra strength right at a nexus
    idw_k: int = 4               # Nearest segments blended for valence/channels
    idw_epsilon: float = 1e-3    # IDW distance floor
    score_frequency: float = 3.0    # Nexus-score FBm frequency (cycles around the torus)
    valence_frequency: float = 1.5  # Valence FBm frequency; low = clustered regions
    floor_frequency: float = 2.0    # Magic-floor FBm frequency
    floor_strength: float = 0.1     # Magic-floor amplitude so dead zones still flicker


# ---------------------------------------------------------------------------
# Biomes (Phase 4)
# ---------------------------------------------------------------------------


@dataclass
class BiomeConfig:
    """Soft biome weighting from climate via inverse-distance weighting."""

    blend_sharpness: float = 4.0   # IDW exponent; higher = sharper single-biome dominance
    weight_cutoff: float = 0.02    # Drop biome weights below this, then renormalize


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------


@dataclass
class WorldgenConfig:
    """Top-level config for the entire worldgen pipeline."""

    seed: int = 0  # Master RNG seed; sub-seeds are derived per stage
    size: int = 100  # Gameplay grid edge length in tiles
    mesh: MeshConfig = field(default_factory=MeshConfig)  # Voronoi simulation mesh
    plates: PlatesConfig = field(default_factory=PlatesConfig)  # Plate partitioning and boundary uplift
    sea_level: SeaLevelConfig = field(default_factory=SeaLevelConfig)  # Land/ocean split and normalisation
    erosion: ErosionConfig = field(default_factory=ErosionConfig)  # Stream-power erosion loop
    landmass: LandmassConfig = field(default_factory=LandmassConfig)  # Connected-component land classification
    insolation: InsolationConfig = field(default_factory=InsolationConfig)  # Authored energy pattern
    temperature: TemperatureConfig = field(default_factory=TemperatureConfig)  # Lapse rate + maritime moderation
    wind: WindConfig = field(default_factory=WindConfig)
    moisture: MoistureConfig = field(default_factory=MoistureConfig)
    river: RiverConfig = field(default_factory=RiverConfig)
    lake: LakeConfig = field(default_factory=LakeConfig)
    savagery: SavageryConfig = field(default_factory=SavageryConfig)  # Legible danger blend
    leyline: LeylineConfig = field(default_factory=LeylineConfig)  # Nexuses + magic web
    biome: BiomeConfig = field(default_factory=BiomeConfig)  # Soft biome weights from climate
