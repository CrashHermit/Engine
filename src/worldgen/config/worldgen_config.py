from __future__ import annotations

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
    growth_raggedness: float = 2.0  # Random cost added to heap priority for organic borders; 0 = round blobs
    continental_fraction: float = 0.45  # Probability each plate is continental vs oceanic
    continental_uplift: float = 1.0  # Base uplift rate assigned to continental plates
    oceanic_uplift: float = 0.0  # Base uplift rate assigned to oceanic plates
    belt_width: int = 4  # BFS hops to smear boundary collision/rift intensity into mountain belts
    belt_strength: float = 0.8  # Multiplier on convergent (collision) boundary uplift
    rift_strength: float = 0.3  # Multiplier on divergent (rift) boundary uplift reduction
    belt_noise_scale: float = 0.5  # Amplitude of noise modulating smeared belt intensity
    uplift_noise_floor: float = 0.05  # Minimum fbm noise multiplier so oceanic plates are not perfectly flat


# ---------------------------------------------------------------------------
# Erosion
# ---------------------------------------------------------------------------


@dataclass
class ErosionConfig:
    """Stream-power erosion and hillslope diffusion on the mesh."""

    iterations: int = 50  # Number of flood-route-erode-diffuse passes
    dt: float = 0.1  # Implicit solver timestep; stable at large values unlike explicit erosion
    K: float = 0.3  # Stream-power erosion coefficient (higher = more valley carving)
    m: float = 0.5  # Drainage-area exponent in the stream-power law
    diffusion: float = 0.08  # Hillslope relaxation toward neighbour mean per pass
    base_level_fraction: float = 0.1  # Lowest elevation percentile treated as provisional ocean for routing
    initial_scale: float = 1.0  # Scales uplift when seeding terrain height before the erosion loop
    initial_noise_amplitude: float = 0.05  # Small noise added to the initial height field


# ---------------------------------------------------------------------------
# Sea level
# ---------------------------------------------------------------------------


@dataclass
class SeaLevelConfig:
    """Percentile cut that converts raw elevation to is_land."""

    target_land_fraction: float = 0.32  # Desired fraction of land cells after sea-level placement


# ---------------------------------------------------------------------------
# Landmass labeling
# ---------------------------------------------------------------------------


@dataclass
class LandmassConfig:
    """Size thresholds for classifying connected land components."""

    island_min_fraction: float = 0.005  # Minimum land fraction to count as an island (class 1)
    landmass_min_fraction: float = 0.08  # Minimum land fraction to count as a major landmass (class 2+)


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
