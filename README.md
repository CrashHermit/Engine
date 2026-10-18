# World generation

Run the interactive globe:

```bash
uv run python -m src.worldgen --layer convergence
```

Render actual radial terrain relief:

```bash
uv run python -m src.worldgen --layer elevation --terrain-relief \
  --vertical-exaggeration 50 --sea-level
```

Relief is optional and affects only the final `elevation` layer. Shared dual
vertices use the mean elevation of their three incident cells, converted through
`GeneratedWorld.radius_m`. The default exaggeration is 1 (true scale); display
controls provide relief and sea-level toggles and a 1–100 exaggeration slider.
The sea-level shell stays at radius 1. Other layers stay flat, and generated
elevations are never changed by display settings.
The translucent water shell uses a cached 512-by-512 sphere, created only when
first enabled. Its vertices lie at sea level; flat triangle interiors still sit
slightly below the ideal sphere (approximately 134 m maximum at Earth radius).
This replaces the coarse shell whose facets intersected kilometres of seafloor
and produced bands at true scale. Toggling water does not regenerate the mesh.

Elevation colour policy is independent of generation settings. Elevation and
coastal-elevation use deep-to-shallow bathymetry colours below zero, a pale
sea-level anchor, and hypsometric land colours from green lowlands through
ochre and brown highlands to pale summits. For comparisons, fix both limits:

```bash
uv run python -m src.worldgen --layer elevation --terrain-relief \
  --elevation-min -8000 --elevation-max 8000
```

Create an offscreen full-rotation GIF using the same display settings:

```bash
uv run python -m src.worldgen --seed 2026 --frequency 40 \
  --layer elevation --terrain-relief --vertical-exaggeration 25 \
  --no-hex-edges --elevation-min -12000 --elevation-max 10000 \
  --rotation-gif /tmp/planet-rotation.gif \
  --rotation-frames 120 --rotation-fps 24
```

`--rotation-gif` automatically uses offscreen rendering. The generated GIF
contains the selected layer and does not regenerate the world between frames.

These display limits do not modify heights or sea level. Without an override,
the viewer uses the configured conservative bounds. `LayerStyle` in
`render/layers.py` owns scalar values, colours, ranges, titles and unit labels;
PyVista actors and controls stay in `render/viewer.py`.


The interactive window has clickable layer selectors on the left. One layer
is active at a time; switching preserves the camera and reuses the same world.
The “hex outlines” checkbox toggles cell edges and retains its setting across
layer changes. Outlines are on by default; use `--no-hex-edges` to start with them
hidden. This changes only the edge overlay, not cell colours, surface geometry,
or tectonic boundary diagnostic lines.
Available layers include `plates`, `hotspot-potential`, `volcanic-potential`,
`volcanic-activity`, `volcanic-areas`, `volcano-state`, `velocity`,
`convergence`, `divergence`, `shear`, `crust`, `crust-regions`, `crust-field`,
`crust-density`, `crust-region-density`, `boundary-sections`,
`subducting-plate`, `coastal-elevation`, `tectonic-relief`, `volcanism`,
`impact-relief`, `terrain-variation`, `elevation`, and `margin-distance`. `crust`
oceanic material in blue and continental material in tan; `crust-regions` shows
region ownership; density layers show dimensionless effective-density proxies.
Boundary sections retain geometric/material continuity and a preferred subducting side,
not discrete interaction categories. `coastal-elevation` displays the continuous
coastal contribution in metres with sea level at zero; `elevation` adds coastal,
tectonic, volcanic, impact, and terrain-variation contributions. `impact-relief`
shows the signed continuous crater bowls and rims. `ElevationConfig.impacts`
controls source count and radius/depth/sharpness/rim/apron parameters; source locations
are seeded independently on the sphere rather than tied to mesh cells.
`margin-distance` is signed distance as a percentage of circumference (positive
continental, negative oceanic). `--layer` selects the initial view. Use `--seed 123`
and `--frequency 20` to control the generated world and mesh resolution. Offscreen
screenshots omit controls.

Plates and crust default to connected, noise-biased priority flooding. Run a
higher-resolution crust view:

```bash
uv run python -m src.worldgen --seed 2026 --frequency 40 --layer crust
```

Each seed gets an independent continuous OpenSimplex2S fBm field sampled on the
unit sphere. Its cell priority is spherical angular distance from that seed
minus `influence` times its noise. Growth advances through the lowest frontier
barrier; crossing a cell retains the maximum priority encountered along that
growth path. Claimed cells cannot be stolen, and seed cells are protected.
This is competitive, graph-based flooding, not ordinary Voronoi assignment or
a globally optimal minimax partition. Every region stays connected to its seed.
Ownership remains discrete; changing the generation mesh can change geography.
Sampling the retained elevation field more finely does not rerun that growth.

Plate growth, crust growth, volcanic potential, and impact sources use independent
fields. Priority flooding remains the default: each plate or crust seed uses its own
noise-biased priority map, configured by that generator's `flood` settings. The
retained Dijkstra plate option samples a plate-owned cost field instead.
Existing random streams keep their roles: plate motion uses child 9, volcanic
potential uses child 0, hotspot source sampling uses child 11, and impact placement
uses appended child 14.

Noise sampling uses `pyfastnoiselite==0.0.7` through its public
`FastNoiseLite.gen_from_coords` API, with an independent generator per field.
Coordinates are paired XYZ columns in a contiguous float32 array, not a Cartesian
grid. Built-in fractal processing is disabled and the native frequency is 1.0:
`field/noise.py` retains the existing manual octave frequencies, amplitudes, and
coordinate shifts, accumulating sampled values in float64.
World seed streams remain signed 64-bit; each field seed wraps modulo 2^32 into
FastNoiseLite's signed 32-bit range. Seeds separated by 2^32 therefore produce the
same raw noise field. No module-global generator state is changed.
This replaces the previous OpenSimplex package entirely. Raw fBm sampling retains
the accepted OpenSimplex2S algorithm and octave settings. `normalized_noise` now
uses a fixed octave-amplitude bound rather than the extrema of each requested
batch, so querying a subset or a single point cannot change its value.
This changes hotspot placement weights and the optional Dijkstra plate cost
field; default priority-flood plate and crust ownership remain unchanged.

Each plate receives a seeded random tangent direction at its normalized mean
cell position and an angular speed uniformly sampled between
`PlateConfig.min_angular_speed=0.05` and `max_angular_speed=0.20`.
The Euler rotation is the cross product of that center and its selected tangent
velocity, with no added center-axis spin. `motion_scale` multiplies all rotations.
CLI controls are `--plate-min-speed`, `--plate-max-speed`, and
`--plate-motion-scale`. Cell velocities and boundary interactions use the same
rotations without normalization. Arrow size remains a separate `--arrow-scale`
display setting. These are procedural units, not physical force or metres per
second.


`PlateConfig.flood` and `CrustConfig.flood` each contain a `PriorityFloodConfig`:
influence `1.1`, five octaves, base frequency `1.4`, lacunarity `2.0`, and
persistence `0.6`. All regions use the same algorithm and settings, with distinct
noise realizations. The CLI independently exposes `--plate-flood-influence` and
`--crust-flood-influence`.

The original distance-weighted Dijkstra algorithm is retained as
`field.partition.weighted_regions`. Select either method independently with
`--plate-growth` and `--crust-growth`, or set each config's `growth_method`:

```bash
uv run python -m src.worldgen --plate-growth dijkstra --crust-growth dijkstra \
  --plate-irregularity 10 --crust-irregularity 10 --layer crust
```

The irregularity flags apply only to Dijkstra, defaulting to `1`. Low field
values are cheap to cross and high values costly; strength controls cost
contrast, not boundary jaggedness. Flood influence is a separate parameter.

Save a diagnostic without opening a window:

```bash
uv run python -m src.worldgen --layer shear --off-screen --screenshot /tmp/shear.png
```

Boundary interactions evaluate both plates' rotation at the same normalized edge
midpoint. Convergence and divergence are the closing and opening components
across the boundary; shear is unsigned. Boundary sections group adjacent dual
edges by ordered plate pair and crust-side types, independently of local motion.
Effective crust density is dimensionless: continental base 1.0, oceanic base 2.0,
with independent smooth variation. Oceanic crust is preferred beneath continental
crust; oceanic/oceanic polarity uses representative regional densities with the
lower plate ID breaking ties. Continental/continental sections have no subducting side.
Elevation reads motion and crust properties directly; no boundary-kind categories remain.
Boundary diagnostics use an opaque globe to hide rear-facing lines and named
categorical legends. Worlds with no plate boundaries display “No boundaries”.

Crust also exposes a read-only `density_anomaly`, relative to each cell's crust-type
baseline rather than absolute density. `config.elevation.coastal.buoyancy` is a
`BuoyancyConfig` with `continental_height_percent=0.02` and
`oceanic_height_percent=0.04`, both percentages of radius per unit relative anomaly.
Less-dense crust raises the continental interior target or makes the ocean basin
shallower; denser crust does the opposite. A 20% anomaly corresponds to roughly
255 m on land or 510 m in the deep ocean at Earth radius.
The coastal blend tapers these changes into the existing profile: nominal
coastline and shelf-break depth are unchanged, and no whole-plate offset or
sea-level adjustment is applied. Set both response coefficients to zero to
disable buoyancy. This is a procedural buoyancy response, not physical isostasy;
crust thickness and thermal history are not modeled.


For Dijkstra, plates use `PlateConfig.field` and crust regions use
`CrustConfig.field`, each a `NoiseConfig`, to set spherical-distance traversal costs.
Each edge's geometric
distance is multiplied by `1 + irregularity_strength * average(endpoint field
values)`. The generic Dijkstra partitioner and cost model are unchanged, but its
plate cost field is now independent of volcanic potential and uses the plate
growth noise stream. This can change maps generated with the Dijkstra option;
default priority-flood maps are preserved.
`WorldgenConfig.geology` composes `PlateConfig`, `CrustConfig`, and `HotspotConfig`
as `plates`, `crust`, and `hotspots`. Crust defaults to 18 continental and 33
oceanic seeds. `CrustConfig.field` defaults remain `octaves=3`,
`base_frequency=1.0`, `lacunarity=2.0`, and `persistence=0.35`; the separate
`flood` settings apply to priority flooding. Seeds are jointly spaced and randomly
assigned exactly those type counts; cells inherit their region's type.
`GeneratedWorld.geology` retains the plate and boundary arrays and
includes a `crust` result with region IDs, seeds, region types, a continental mask,
and a read-only normalized `shaping_field`. In flood mode that diagnostic samples
each cell's winning region priority; it is not a shared noise or arrival-time field.
Seed counts do not guarantee area percentages or separate continents.
`GeneratedWorld.elevation` retains read-only `coastal_elevation`,
`tectonic_relief`, `volcanic_relief`, `terrain_variation`, and final `elevation` arrays.
Elevation values use zero as their sea-level datum; no land/sea classification
is returned.
Elevation uses exact finite spherical boundary arcs rather than graph propagation.
Continental collisions and subduction combine coherent section responses through
positive/negative envelopes. Motion and side influence blend continuously between
nearby arc sources. Divergence and transform add separate signed contributions.
`WorldgenConfig.elevation.deformation` groups four independent process settings:
`collision`, `subduction`, `divergence`, and `transform`. Collision defaults to
`width_percent=2.5` and `height_percent=0.16`; subduction defaults to
`width_percent=2.5`, `height_percent=0.15`, and `trench_depth_multiplier=2.25`.
These heights are percentages of radius per unit raw interaction strength.
Divergence defaults to `width_percent=1.0` and `height_percent=0.075`. Width is
the reach on each side: at Earth radius the default divergence reach is
approximately 400 km per side.
Changing one process's settings no longer changes another process.
No world-maximum normalization is used. Set a process's width or height to zero
to disable that process. These are procedural geological profiles, without
erosion or volcanic simulation.
Profile settings live with their process: crest controls under
`config.elevation.deformation.collision`, trench/arc controls under
`config.elevation.deformation.subduction`, and ridge/rift controls under
`config.elevation.deformation.divergence`. Transform controls live under
`config.elevation.deformation.transform`. There is no duplicate elevation config
under geology and no retained terrain configuration alias.
Continental collision uplift adds a narrower, squared-taper crest on its broad base.
`crest_width_fraction=0.3` confines it to the inner 30% of the propagation width
on each uplifting side (0.75% of circumference with the default width).
`crest_height_multiplier=2.0` adds up to twice the broad source amplitude at the
boundary, for a combined peak coefficient of three times the broad component.
The crest has a pointed cross-section rather than the smoothstep's flat summit.
Setting its height multiplier to zero restores the broad-only profile.

The default collision amplitude and independent trench-depth multiplier are
tuned for an Earth-scale sampled elevation range. They target comparable
mountain and trench extremes without deepening the entire ocean basin or
increasing the overriding volcanic arc by the same factor. They remain
procedural profiles, not a physical plate-tectonics simulation.
Trenches and divergent relief are unaffected. Actual sampled heights depend on
motion strength and cell distance from the boundary; coarse meshes can miss the
crest entirely. Use frequency 40 or higher to inspect the narrow component.

Subduction uses `subduction_profile` from `profiles.py`, for both oceanic–oceanic
and oceanic–continental boundaries. It takes signed distance: negative on the
descending side, positive on the overriding side. `trench_width_fraction=0.2`
sets the trench reach on each side of a shared floor at distance zero.
`trench_depth_multiplier=2.25` deepens that floor independently of the overriding
arc amplitude.
On the overriding side, a compact smooth arc peaks at `arc_offset_fraction=0.25`
of that width inland from the boundary, with half-width `arc_width_fraction=0.2`
and amplitude `arc_height_multiplier=1.5` times the source amplitude.
The overriding forearc rises continuously from the trench into the arc; no
collision crest is added. Arc variation multiplies only the volcanic component,
not the trench or forearc depression. The arc fades to zero at the boundary even
when its configured support overlaps the trench floor.
These widths and offsets follow the existing percentage-of-circumference scale.
`utilities/curves.py` owns generic curve math: `clamp_unit` and
`smoothstep_scalar` serve per-cell scalar profiles, while NumPy `smoothstep`
handles coastal and volcanic shield arrays. Scalar profiles avoid array
operations without changing the clamped cubic curve.

An independent simplex field varies arc heights using `arc_variation_strength=0.6`
and `arc_noise_frequency=6.0`, sampled on unit-sphere positions without sample
normalization. It affects only overriding arcs, not trenches, collisions or
divergence. A new SeedSequence child 10 preserves all earlier streams.
Arc crests may remain submerged or emerge according to final elevation relative
to zero; there is no forced island threshold or sea-level adjustment.
Subduction uses nearest distance within each coherent section and a compact,
arc-length-weighted blend of source motion. The two signed profiles crossfade
near the boundary and its endpoints, avoiding discontinuous source-side switches.


Divergence is evaluated independently on each side for every crust pairing.
`profiles.py` provides `divergent_response` (continental negative, oceanic positive)
and `divergent_profile`. Oceanic sides have a broad raised ridge with a narrower
axial valley; continental sides have a central trough and raised shoulders.
`axial_width_fraction=0.25` sets the axial feature width relative to the broad
propagation width. `axial_depth_multiplier=0.65` sets the axial depression relative
to the source amplitude; zero removes it, allowing a ridge without an axial valley.
`shoulder_height_multiplier=0.35` controls continental rift shoulders.
These are stylized cross-sections, not spreading-rate or mechanical simulations.
The oceanic axis can remain elevated above the distant basin while lying below
the ridge flanks. All profiles taper to zero at the configured outer width.

Divergence uses exact nearest distance to its retained active boundary sources,
with compact, arc-length-weighted blending of motion and material response.
The profile uses that one distance rather than maximizing every edge's flank,
so distant flanks do not fill the axial valley.
Narrow axial features require enough mesh resolution to be sampled.

`WorldgenConfig.elevation` composes independent `CoastalConfig` and
`DeformationConfig` settings as `coastal` and `deformation`. Coastal evaluators
receive only `CoastalConfig`; tectonic evaluators receive only `DeformationConfig`.
`WorldgenConfig.elevation.coastal` contains three `CoastalWidthConfig` settings:
`inland`, `shelf`, and `slope`, with `base_percent` defaults 2.0, 1.25, and 1.25.
Each base width is a percentage of circumference; they do not sum to 100%.
Each width independently exposes `variation_strength=0.3` and
`noise_frequency=1.0`. A single-octave 3D simplex field sampled on unit-sphere
positions multiplies the base width by `1 + variation_strength * noise`.
Strength 0.3 permits 70–130% of the base width; zero restores uniform widths.
Use strengths below 1 to retain positive widths. Independent seeded streams
are appended for the three fields, preserving the plate/crust sampling streams.
Noise is not normalized against sampled extrema, so resampling a position
preserves its width. The shelf break stays at the crust boundary; variable
shelf width also changes the inland coastline offset. Variation changes widths,
not interior heights or basin depths. Configure individual fields using
`dataclasses.replace`, for example:

```python
coastal = replace(
    config.elevation.coastal,
    shelf=replace(
        config.elevation.coastal.shelf,
        variation_strength=0.6,
        noise_frequency=1.5,
    ),
)
config = replace(config, elevation=replace(config.elevation, coastal=coastal))
```

Angular edge distances are converted directly to percentages, with no physical
radius or tile-count dependency. Coastal elevation magnitudes are percentages of
radius, configured on `WorldgenConfig.elevation.coastal`:
`interior_height_percent=0.00942`, `shelf_depth_percent=0.00314`, and
`basin_depth_percent=0.08063`. Depth parameters are positive and subtracted by
the profile. `WorldgenConfig.planet` is a `PlanetConfig` with
`radius_m=6_371_000.0`; these defaults produce approximately +600 m, -200 m,
and -5,137 m. A percentage value of `1.0` means 1%, not a fraction of 1.
Generated elevation and `ElevationResult.elevation_range_m` are in metres;
the viewer uses that configured range rather than fixed height limits.
Doubling the radius doubles elevations and implied physical horizontal distances,
without changing unit-sphere noise, ownership, or coastlines. Increasing only
the elevation percentages increases relief. No physical radius is used for noise
sampling. These profile settings are artistic choices, not universal physical
constants. Signed crust-margin distance is exact angular distance to the nearest
finite arc in the extracted continental–oceanic boundary network, positive on
continental crust and negative on oceanic crust. The shelf break lies at the
crust boundary; the coastline is offset inland by one local shelf width.
Sampling at finer resolution resolves the same established geography.

`WorldgenConfig.elevation.variation` controls a fourth, additive elevation
component: a global continuous noise field, evaluated at the sampled spherical
positions. `amplitude_percent=0.0215` bounds its displacement to ±0.0215% of
planet radius (about ±1,371 m at the default radius). Its independent
`NoiseConfig` defaults to four octaves, base frequency 4.0, lacunarity 2.0, and
persistence 0.5. The generator assigns it an appended deterministic seed stream;
existing geology and elevation streams are unchanged. Set the amplitude to zero
to produce exactly zero variation without sampling noise.

Final elevation is the sum of coastal elevation, tectonic relief, volcanic relief,
and terrain variation. The variation is applied globally, not faded near coasts:
it may therefore move the final sea-level coastline, but it does not change crust
ownership, extracted boundaries, or the other elevation components. Its amplitude
is bounded in metres and scales with planet radius.

Transform relief combines existing normal and shear boundary motion without a
discrete transform classification. Closing plus sliding produces restraining
uplift; opening plus sliding produces a releasing basin. Pure sliding and pure
normal motion produce no transform contribution. The signed strength is the
normal component multiplied by the shear fraction of their combined magnitudes;
it is not normalized against a world maximum.
The pure `transform_strength` helper computes the coupling. `TectonicField`
uses normalized source blending without stacking every boundary edge; bounds use
the retained maximum relative rotation magnitude.

`TransformConfig` defaults to `width_percent=0.75` of circumference per side
(approximately 300 km at Earth radius) and `height_percent=0.05` of radius per
unit coupled strength. A compact smooth profile uses nearest active source distance
and blended signed strength, then adds its response to the other processes.
Set either setting to zero to disable it independently.
This is a broad procedural transpression/transtension response, not a fault
mechanics simulation: it uses the sampled local motion components, does not move
cells sideways, and does not explicitly reconstruct bends or displacement history.

Intraplate volcanism uses `config.geology.hotspots` (`HotspotConfig`).
It samples 12 spaced interior cell centres by default, outside a plate-boundary
clearance of 1.25% of circumference. `min_seed_distance=0.3` is a unit-sphere
chord distance. Placement weights are `1 + potential_bias * potential`, with
`potential_bias=4.0`; setting the bias to zero removes the field preference.
Hotspot generation owns `config.geology.hotspots.potential`, a `NoiseConfig`
with `octaves=5`, `base_frequency=0.3`, `lacunarity=3.0`, and `persistence=0.5`.
The sampled fBm field is normalized to [0, 1] and retained read-only as
`world.geology.hotspots.potential`. `PlateConfig.field` uses the same small
noise-settings type, but samples its independent field only for Dijkstra costs.
There is no simulated convection or flow-vector stage.

Each source independently samples a shield radius between `min_width_percent=0.5`
and `max_width_percent=1.0` of circumference, and uplift between
`min_height_percent=0.03` and `max_height_percent=0.1` of radius. Volcanic potential
does not multiply the sampled height; density affects only the existing base surface.
The independent hotspot RNG uses appended SeedSequence child 11, preserving
all earlier streams. Set `count=0` to disable hotspots.

`geology/hotspots.py` owns source selection and metadata; `VolcanicField` in
`elevation/volcanism.py` retains spherical centers and compact shield profiles.
Shields are confined to their source plate with a continuous taper to zero at
plate boundaries, rather than an abrupt cutoff. Source peaks are retained.
Overlapping shields combine by maximum rather than stacking.
`world.elevation.volcanic_relief` stores uplift in metres; final elevation adds
coastal elevation, tectonic relief, volcanic relief, and terrain variation.
Seamounts, ocean islands, and continental volcanoes emerge from that sum without
a forced sea-level rule.
This models static volcanic systems, not plume drift or time-evolving island chains.

Use `--layer volcanism` to inspect volcanic uplift alone on the diagnostic globe.
Use `--layer elevation --terrain-relief --sea-level --no-hex-edges` to see it in
the final surface. Frequency 80 or higher helps resolve the shield flanks.
Use `--layer hotspot-potential` to inspect the independent hotspot placement noise.
`volcanic-potential` now displays the source-derived field described below.

Volcanic metadata lives in `world.geology.volcanism`, configured by
`config.geology.volcanism` (`VolcanismConfig`). Read-only `hotspot_potential`,
`subduction_potential`, and `divergence_potential` arrays describe compact hotspot
footprints, overriding-side arcs, and narrow divergent axes. Arc widths and offsets
reuse elevation's configured geometry and the same arc-variation samples;
convergence and divergence retain their raw motion scale. Continental divergent
potential is varied by the existing hotspot-placement field. Collision and transform
boundaries do not create volcanic potential by default. The combined `potential`
uses a maximum envelope as a procedural placement policy, not a physical magma law.

`volcanic_mask` marks `potential >= potential_threshold` (default 0.18), including
dormant prospective areas. `activity` instead measures current eruption intensity
around erupting sites; a volcanic area can have zero current activity.
Both are mesh-sampled arrays, not yet arbitrary-coordinate world evaluators.

`sites` retains unique `cell_indices`, `source_types` (`VolcanoSource`), `states`
(`VolcanoState`), `supply_strength`, and `eruption_intensity`. A hex locates its
site through `cell_indices`; overlapping influence does not change site identity.
The generator samples up to `supplied_site_count=24` spaced potential-qualified
sites. `supply_persistence_probability=0.75` determines whether supply persists;
unsupported sites are extinct. Supplied sites erupt with
`eruption_probability=0.08`, otherwise they are dormant. Dormant sites have positive
supply but zero eruption intensity; extinct sites have neither. These probabilities
are artistic snapshot settings, not measured eruption rates or a simulated history.
Site spacing defaults to a unit-sphere chord distance of 0.12.

Up to `historical_extinct_site_count=8` additional historical sites are placed
outside the threshold-qualified belts. Their `HISTORICAL` source type identifies
retained shield geometry: widths 0.35–0.9% of circumference and heights 0.02–0.08%
of radius. They are extinct with no current activity but retain their uplift.
`widths_percent` and `heights_percent` are zero for current-belt sites because
their underlying hotspot, arc, or ridge morphology already exists. Historical
shields combine with hotspot shields by maximum; no duplicate arc/ridge uplift
is added. Eruption state does not remove mountains or alter sea level.
The new snapshot RNG uses child 12, preserving prior stream assignments.

Inspect the site states interactively:

```bash
uv run python -m src.worldgen --seed 2026 --frequency 40 \
  --layer volcano-state --no-hex-edges
```

`volcano-state` marks dormant sites yellow, erupting sites orange-red, and extinct
sites slate gray. `volcanic-activity` shows eruption footprints;
`volcanic-areas` shows the prospective boolean mask. `volcanism` remains the
hotspot-plus-historical shield uplift diagnostic; boundary arcs and ridges remain
in `tectonic-relief`. These fields describe volcanic systems, not individual
eruptions evolving over time.

Elevation lives in the flat `src/worldgen/elevation/` package. `generate.py`
builds an `ElevationField`; `field.py` samples its retained geography and source
definitions into an `ElevationResult`. `coastal.py` retains a `CoastalField`
and evaluates the continent-to-basin profile with `CoastalConfig`.
`profiles.py` contains geological cross-sections. `deformation.py` owns indexed
tectonic evaluation, with process functions in `collision.py`, `subduction.py`,
`divergence.py`, and `transform.py`. In `bounds.py`, `coastal_bounds` and
`tectonic_bounds` derive each contribution's conservative range from its own
configuration; `elevation_bounds` combines those with the volcanic height bound,
without measuring extrema of a requested sample batch.
`TectonicField` retains arc normals and lengths, relative plate rotations,
across-boundary vectors, material sides and section metadata once. Sampling queries
the existing spatial index in batches of at most 1,024 positions and evaluates
their point–arc distances together, rather than invoking NumPy once per position.
`kernels.py` runs the motion, section blending and profile reductions through
Numba's cached `njit` path. Scratch arrays are allocated once per batch and reused
across its positions; scalar process helpers do not construct temporary arrays.
The geological profiles, finite-arc distances, envelopes and blend rules are
unchanged. Floating-point reduction order can produce roundoff-sized differences.
There is no lower-detail approximation or alternate fallback sampling path.
The first uncached call includes compilation; subsequent calls reuse compiled code.
The full elevation sampler also shares its cell-ownership query with shield
evaluation. The Python implementation targets 3.13+.

`src/worldgen/surface/` derives nonnegative land height and water depth from the
full signed elevation (`0 m` is sea level), then measures slope, sampled local
relief, and detrended roughness around each query point. `SurfaceField` samples
the continuous elevation at the center and at eight bearings on a great-circle
ring. Its fixed geographic footprint is `SurfaceConfig.radius_percent`, measured
as a percentage of circumference; the default `0.05%` is about 20,015 m on the
default planet and does not change with mesh spacing. Height, relief, and
roughness are in metres; slope is in degrees. These finite-footprint diagnostics
do not modify elevation or classify land, fill lakes, calculate aspect, or
simulate hydrology.

`geometry/boundary.py` provides the shared geographic representation:
`SphericalRegions` locates the actual centroid-dual cell containing a point,
not simply its nearest center; `BoundaryNetwork` retains shared dual vertex IDs,
side labels, and finite minor great-circle arcs. Spatial indexes accelerate
ownership, exact nearest-boundary distance, and nearby-source queries.
The initial network is not smoothed, preserving the flood-generated adjacency.
Plate IDs remain categorical; elevation is continuously evaluated.

The world orchestrator generates geology, builds `world.elevation_field` and
`world.surface_field`, then samples their center values at `world.mesh.vertices`
to populate `world.elevation` and `world.surface`. The surface pass reuses the
already sampled center elevations and queries only its eight surrounding
positions. Both retained fields can also be queried away from the generation
mesh; sampling does not select new seeds, normalize against requested samples,
or modify established boundaries.

```python
import numpy as np
from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world

world = generate_world(WorldgenConfig(seed=2026, subdivision_frequency=40))
positions = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])  # Nx3 unit vectors
samples = world.elevation_field.sample(positions)
surface = world.surface_field.sample(positions, center_elevation=samples.elevation)
heights_m = samples.elevation
water_depth_m = surface.water_depth
```

`ElevationField.sample` returns read-only `coastal_elevation`, `tectonic_relief`,
`volcanic_relief`, `terrain_variation`, `elevation`, and signed `margin_distance`.
The same point returns the same values when queried alone, reordered, or alongside
a finer sampling mesh. Range metadata is independent of the query batch and
scales with planet radius.

`SurfaceField.sample` returns read-only `land_height`, `water_depth`,
`slope_degrees`, `local_relief`, and `roughness`. Slope is the fitted local-plane
angle; local relief is the sampled maximum-minus-minimum including the center;
roughness is RMS residual after removing that plane. Changing the footprint
changes these measurements, not the underlying elevation or geology. Surface
samples are independent of query order and batch size.

Continuous does not imply differentiable: sharp crests, nearest-distance medial
axes and envelope changes can have slope changes without height jumps. The
generation mesh still limits established coastline detail; denser sampling does
not invent smaller islands or regenerate the priority flood.

Geology still owns plate/crust structure, categorical metadata and volcanic-site
states. Its diagnostics and source placement remain mesh-based. Generic graph
distance machinery in `field/distance.py` remains for those generation stages;
it is no longer the elevation sampling path.

These surface metrics are diagnostics, not detailed terrain simulation.
Hydrology, aspect, climate, and erosion are not implemented here.

Inspect a derived surface diagnostic in the viewer:

```bash
uv run python -m src.worldgen --layer slope
```

Set the physical planet radius from the CLI:

```bash
uv run python -m src.worldgen --radius-m 12742000 --layer elevation
```

Plate generation is composed from `generate_plate_regions`,
`generate_plate_rotation`, `calculate_plate_velocity`, and
`region_boundary_edges` from `field/partition.py`. The boundary operation accepts
any per-cell region labels, including crust regions or continental/oceanic types.
`generate_plates` returns a named `PlateResult`;
the geology orchestrator computes boundary interactions separately.

Generation assumes valid inputs and outputs. No database is required.
The previous implementation remains in `legacy/` for reference.