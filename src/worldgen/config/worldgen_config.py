from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Mesh
# ---------------------------------------------------------------------------


@dataclass
class MeshConfig:
    """Parameters for the Voronoi mesh that underpins all simulation layers."""

    # Target number of Voronoi cells (sites).  0 = derive from world size for
    # ~1 cell per tile (parity), so the gameplay bake neither up- nor down-samples
    # the mesh — tweak ``size`` and the mesh density follows.  Derived as
    # ``min(size * size, cell_count_cap)``; set a positive value to pin it
    # explicitly (tests do this for speed).  Note: changing this reseeds the
    # geometry, so it is part of a world's identity — pin it per saved world.
    cell_count: int = 0
    cell_count_cap: int = 40000  # Ceiling on the size-derived count (gen time ~linear)
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
    # Continental freeboard: continental crust rides high, sloping up from its
    # margins into a buoyant interior platform.  Without it a continental plate
    # is a flat slab balanced at sea level, so only the boundary belts surface
    # and land reads as a stringy skeleton; with it whole continents stand up as
    # blobs and rising sea level floods the low margins first (realistic).
    continental_freeboard: float = 1.1  # Peak interior uplift added to continental cells
    freeboard_reach: float = 0.06  # Inland ramp length to the platform (fraction of span)
    density_jitter: float = (
        0.5  # Per-plate density noise so same-type plates have a definite subducting side
    )
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
    """Emergent sea level from the hypsometric (ocean/continent) datum."""

    # Sea level sits at the Otsu split between the oceanic and continental
    # elevation modes, so land fraction *emerges* per seed rather than being
    # forced to a quota.  ``datum_bias`` shifts it in elevation std-devs
    # (+ raises sea level -> less land); presets bias this, not a quota.
    datum_bias: float = 0.0
    # Guardrails on the realized land fraction so no seed goes all-ocean or
    # all-land.  Widen to (0.0, 1.0) to disable guardrails entirely.
    land_fraction_clamp: tuple[float, float] = (0.25, 0.70)
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
    """Latitude-derived energy pattern on the torus.

    The equator sits at the map center and the poles at the y-wrap seam, so the
    northern and southern hemispheres are mirror images that both lead to the
    same wrapped polar cap.  Insolation is a function of ``|latitude|`` (1 at the
    equator, 0 at the poles) and wraps seamlessly in y.
    """

    bands: int = 1          # Equator-to-pole latitude cycles over the torus height
                            # (1 = a single equator at center, poles at the seam)
    contrast: float = 0.8   # Spread of climate zones; <1 flattens, >1 sharpens
    wobble: float = 0.0     # Low-freq noise warp on the latitude lines; 0 = laser-straight
    # A raw cosine lingers at its peaks, so the band's value distribution is
    # U-shaped (arcsine): fat hot/cold extremes, a starved temperate middle.
    # Raising the cosine to this power (>1) narrows the extreme bands and widens
    # the temperate zone, the way most of a planet is temperate, not polar.
    temperate_bias: float = 2.0  # Cosine shaping exponent; 1.0 = raw cosine (U-shaped)

# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------


@dataclass
class TemperatureConfig:
    """Lapse rate and maritime moderation on top of insolation."""

    lapse_rate: float = 0.3         # Cooling per unit elevation above the lowland datum
    # Lapse is measured above this percentile of land elevation, not sea level:
    # a continental platform that rides high (freeboard) is the thermal baseline,
    # and only relief *above* it (real mountains) cools.  Without this, raising
    # whole continents would freeze their interiors wholesale.
    lapse_datum_percentile: float = 50.0  # Land-elevation percentile used as the lapse datum
    maritime_reach: float = 4.0     # Coast-distance decay length for ocean moderation
    maritime_strength: float = 0.4  # How strongly coasts pull toward sea temperature

# ---------------------------------------------------------------------------
# Ocean currents (sea-surface temperature)
# ---------------------------------------------------------------------------


@dataclass
class OceanCurrentConfig:
    """Wind-advected sea-surface temperature — toroidal ocean currents.

    Heat is seeded from the ocean's latitude baseline (= insolation), advected
    along the prevailing wind over the *ocean-only* graph (land is a barrier, so
    currents deflect along coasts and gyres/circumpolar bands emerge), and
    relaxed back toward the baseline at the air-sea thermal relaxation rate.  No
    Coriolis is faked: the warm-coast/cold-coast asymmetry comes from the wind's
    meridional sign plus continent geometry.  See
    ``docs/worldgen-ocean-currents-plan.md``.
    """

    passes: int = 40           # advect+relax iterations to steady state
    relaxation: float = 0.05   # air-sea relaxation fraction per pass (physical
                               # timescale; smaller = currents reach further)


# ---------------------------------------------------------------------------
# Wind
# ---------------------------------------------------------------------------


@dataclass
class WindConfig:
    """Prevailing wind belts and terrain deflection (three-cell circulation)."""

    zonal_strength: float = 1.0        # East-west belt amplitude (trades/westerlies)
    meridional_strength: float = 0.3   # North-south component amplitude
    turbulence: float = 0.4            # FBm wobble amplitude on each component
    deflection: float = 0.5            # How hard wind bends away from uphill (step 4)
    convergence_percentile: float = 90.0  # Wind-convergence percentile mapped to 1.0
    # Convergence is a climatic normal, so smooth the raw (turbulence-noisy)
    # divergence into the belt/terrain-scale signal that bands the rain.  This is
    # stage one of the two-stage precipitation de-marbling (the precip output
    # smooth is stage two): killing the convergence-door noise early, before it
    # bakes into sharp wet/dry contrast, lets the final precip smooth stay gentle.
    convergence_smoothing_passes: int = 6     # Laplacian passes on the convergence field
    convergence_smoothing_strength: float = 0.5  # Blend toward neighbour mean per pass

# ---------------------------------------------------------------------------
# Moisture
# ---------------------------------------------------------------------------


@dataclass
class MoistureConfig:
    """Geography-driven precipitation (a climate normal).

    precip = belt(latitude) x continentality(coast, sst) x orographic(wind, relief)
    x (1 + perturb*convergence), composed multiplicatively, absolute-calibrated
    with no floor.  See docs/worldgen-precipitation-redesign-plan.md.  This replaces
    the old iterative moisture advection, which flooded the continent uniformly and
    needed a precipitation floor to avoid all-desert interiors.
    """

    # --- latitude belt (Hadley structure): wet ITCZ + temperate, dry subtropics/poles ---
    belt_equator_weight: float = 1.0    # Equatorial (ITCZ) wet-bump weight
    belt_equator_sigma: float = 0.24    # Equatorial bump width in |latitude|
    belt_temperate_weight: float = 0.8  # Temperate wet-bump weight
    belt_temperate_center: float = 0.55  # Temperate bump center in |latitude|
    belt_temperate_sigma: float = 0.2   # Temperate bump width in |latitude|
    belt_floor: float = 0.12            # Faint precip even in the driest belts (never 0)
    # --- continentality + ocean source (wet coasts, dry interiors; cold-current deserts) ---
    continentality_reach: float = 10.0  # Inland reach to 1/e supply, in map-width units (density-independent)
    sst_source_min: float = 0.30        # Driest coastal source (cold current) as a fraction of warm
    sst_source_gamma: float = 1.0       # Shapes the warm->wet / cold->dry coastal response
    # --- orographic: windward wet, leeward rain shadow (extended via upwind barrier) ---
    orographic_lookahead: int = 6       # Cells scanned upwind along the wind for a barrier
    shadow_strength: float = 3.0        # How hard an upwind barrier dries the lee (per elev unit)
    windward_gain: float = 0.6          # Wet bonus per unit upslope into the wind
    orographic_min: float = 0.2         # Floor on the orographic multiplier (never fully zero)
    orographic_max: float = 1.6         # Cap on the windward wet bonus
    # --- convergence perturbation (secondary; the belt carries the bands) ---
    convergence_perturb: float = 0.25   # +/- fraction the smoothed convergence field nudges precip
    # --- final shaping (absolute; no floor, no relative anchor) ---
    precip_gamma: float = 0.8           # >1 sharpens arid, <1 lifts arid
    smoothing_passes: int = 1           # Light Laplacian to clean mesh-walk artifacts (0 = off)
    smoothing_strength: float = 0.5     # Blend toward neighbour mean per pass


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
    """Legible danger as a weighted blend of named geography components.

    Savagery is *physical/geographic* danger only and is deliberately orthogonal
    to magic: how magical a place is lives in ``magic_strength``/``magic_channels``,
    not here.  A place can be quiet-but-savage or steeped-in-magic-but-calm; a
    future encounter/threat layer is what composes the axes
    (``total_threat = f(savagery, magic_strength, ...)``).
    """

    remoteness_weight: float = 0.35   # coast_distance, max-normalized
    harshness_weight: float = 0.30    # climate distance from comfort (0.55, 0.5)
    ruggedness_weight: float = 0.15   # slope, percentile-normalized
    noise_weight: float = 0.20        # FBm surprise
    volcanism_weight: float = 0.15    # live volcanic ground (arcs, ridges, hotspots) is dangerous
    comfort_temperature: float = 0.55  # Most-comfortable temperature (harshness origin)
    comfort_precipitation: float = 0.5  # Most-comfortable precipitation (harshness origin)
    ruggedness_percentile: float = 95.0  # Percentile that normalizes slope to 1.0
    noise_frequency: float = 3.0      # Surprise-noise spatial frequency (relative to span)
    # Savagery is consumed as discrete bands, so single-tile flips read as
    # confetti; a light Laplacian smooth removes them while keeping the intentional
    # noise-term texture.  Start light (2) and raise toward ~4 only if band-confetti
    # persists.  (It also self-heals partly: harshness reads the now-smoothed precip.)
    smoothing_passes: int = 2         # Laplacian passes on savagery (0 = off)
    smoothing_strength: float = 0.5   # Blend toward neighbour mean per pass


# ---------------------------------------------------------------------------
# Magic (Phase 4) — mana hydrology
# ---------------------------------------------------------------------------


@dataclass
class MagicConfig:
    """Mana hydrology: ley-mantle potential, rock coupling, emission, veins.

    Magic is generated like water: an emission flows down a ``combined_potential``
    (a low-frequency ley-mantle field perturbed by the rock 'bones') and
    accumulates into dendritic veins, exactly as discharge accumulates into
    rivers.  See ``docs/worldgen-magic-redesign-plan.md``.
    """

    ley_mantle_frequency: float = 1.2   # Low → broad source/sink regions (the climate baseline)
    ley_mantle_octaves: int = 3         # FBm octaves for the ley-mantle field
    bones_weight: float = 0.6           # How hard faults/ridges carve troughs into the potential
    bones_boundary_weight: float = 1.0  # Fault stress (convergence + divergence) share of bones
    bones_ridge_weight: float = 0.5     # Ridge-line (high-slope) share of bones
    bones_ridge_percentile: float = 80.0  # Slope percentile that counts as a ridge
    bones_smoothing: int = 1            # Laplacian passes on the bones field (0 = off)
    bones_smoothing_strength: float = 0.5  # Blend toward neighbour mean per bones pass
    ambient_floor: float = 0.05         # Uniform emission so dead zones still flicker
    base_fraction: float = 0.10         # Lowest-potential percentile used as routing base (sinks)
    channel_frequency: float = 1.5      # Per-channel noise freq (clustered corpus/mens/anima-lands)
    nexus_prominence: float = 0.15      # Min normalized prominence to enumerate an extremum as a pole
    nexus_min_spacing: float = 0.08     # Greedy pole spacing as a fraction of world span
    vein_percentile: float = 90.0       # Strength percentile that counts as a vein
    flow_strength_exp: float = 0.2      # Mana-current speed ∝ strength^this
    flow_slope_exp: float = 0.3         # Mana-current speed ∝ potential-slope^this


# ---------------------------------------------------------------------------
# Vulcanism (Phase 1.5 — between boundary uplift and erosion)
# ---------------------------------------------------------------------------


@dataclass
class VulcanismConfig:
    """Subduction arcs, hotspot island chains, and rift/ridge volcanism.

    Runs after boundary uplift and before erosion, so its edifices are dissected
    and drained like the rest of the terrain.  Reads the shared ``BoundaryFacts``.
    """

    # --- subduction arcs (on the overriding plate, offset inland) ---
    arc_uplift: float = 0.9          # Arc edifice height per unit convergence
    arc_offset: int = 3              # BFS hops inland from the trench to the arc crest
    arc_width: int = 2               # Arc band half-width in hops (falloff each side)
    arc_volcano_spacing: float = 0.07  # Min spacing between arc volcanoes (span fraction)
    dormant_fraction: float = 0.3    # Fraction of arc volcanoes rolled dormant

    # --- hotspots (drift-aligned decaying island trails) ---
    hotspot_count: int = 4           # Number of mantle hotspots
    hotspot_continental_fraction: float = 0.2  # Share allowed on continental plates
    hotspot_spacing: float = 0.2     # Min spacing between hotspots (span fraction)
    chain_length: int = 6            # Volcano stamps per hotspot trail
    chain_step: float = 0.025        # Trail spacing along drift (span fraction)
    chain_decay: float = 0.72        # Height/activity multiplier per stamp down-trail
    hotspot_peak_uplift: float = 1.0  # Active-head edifice height

    # --- rifts / mid-ocean ridges ---
    ridge_uplift: float = 0.4        # Oceanic-divergent ridge raise per unit divergence
    rift_flank_strength: float = 0.5  # Continental-rift volcanism field weight
    rift_volcano_spacing: float = 0.10  # Min spacing between rift/ridge volcanoes (span)

    # --- shared ---
    volcano_smear: int = 1           # BFS hops the radial edifice bump spreads
    bump_falloff: float = 0.5        # Edifice bump multiplier per smear hop
    caldera_fraction: float = 0.18   # Fraction of volcanoes with a crater lake (VP2)
    max_per_chain: int = 2           # Discrete volcanoes kept per arc/hotspot chain (landmark scale)
    max_volcanoes: int = 18          # Global cap: keep only the most prominent breached edifices


# ---------------------------------------------------------------------------
# Biomes (Phase 4)
# ---------------------------------------------------------------------------


@dataclass
class BiomeConfig:
    """Soft biome weighting from climate via inverse-distance weighting."""

    blend_sharpness: float = 4.0   # IDW exponent; higher = sharper single-biome dominance
    weight_cutoff: float = 0.02    # Drop biome weights below this, then renormalize
    # A hard argmax over the soft weights turns cell-scale climate wiggle into
    # salt-and-pepper biomes (every band-boundary crossing flips). Diffusing the
    # soft membership over land neighbours first makes biomes coherent regions
    # with gradual ecotones, the way real biomes blend, without erasing variety.
    # With precipitation now smoothed to a climatic normal upstream, this pass no
    # longer has to fight marbling — its only remaining job is to soften the hard
    # argmax band-edge line into a gradual ecotone, so it runs light.
    smoothing_passes: int = 2      # Laplacian passes on the soft weights (0 = off)
    smoothing_strength: float = 0.5  # Blend toward the land-neighbour mean per pass [0,1]


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
    vulcanism: VulcanismConfig = field(default_factory=VulcanismConfig)  # Arcs, hotspots, ridges
    landmass: LandmassConfig = field(default_factory=LandmassConfig)  # Connected-component land classification
    insolation: InsolationConfig = field(default_factory=InsolationConfig)  # Authored energy pattern
    temperature: TemperatureConfig = field(default_factory=TemperatureConfig)  # Lapse rate + maritime moderation
    ocean_current: OceanCurrentConfig = field(default_factory=OceanCurrentConfig)  # Wind-advected sea-surface temperature
    wind: WindConfig = field(default_factory=WindConfig)
    moisture: MoistureConfig = field(default_factory=MoistureConfig)
    river: RiverConfig = field(default_factory=RiverConfig)
    lake: LakeConfig = field(default_factory=LakeConfig)
    savagery: SavageryConfig = field(default_factory=SavageryConfig)  # Legible danger blend
    magic: MagicConfig = field(default_factory=MagicConfig)  # Mana hydrology (ley-mantle → veins)
    biome: BiomeConfig = field(default_factory=BiomeConfig)  # Soft biome weights from climate
