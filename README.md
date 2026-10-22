# World generation

The world is defined by continuous fields in Cartesian 3D. The globe and hex mesh are sampling and presentation surfaces; neither defines the underlying geology.

## Generation model

`generate_world_field(config)` builds a mesh- and planet-radius-independent `WorldField`. `WorldField.sample_world(points)` accepts arbitrary `N × 3` coordinates and returns a `WorldSample` containing named geology and elevation arrays. `generate_world(config)` creates an icosphere, samples those fields at its vertices, and derives surface measurements. Each field query is deterministic, batch-independent, and does not mutate NumPy's global random state.

The common coordinate frame is the centered Cartesian cube `[-1, 1]³`. The planet is the unit sphere in that frame. A single volumetric shear warp is applied to world query points before sampling source geology and elevation:

```text
source_position = W(world_position)
world_elevation = source_elevation(source_position) + terrain_variation(world_position)
```

Terrain variation is intentionally sampled in world coordinates after the geological warp. Geometry is not projected onto the sphere during field construction. `WorldField.sample_elevation_meters(points, radius_m=...)` converts the radius-fraction elevation into meters.

`RegionRotationField` owns an unwarped source partition. Both `sample(source_positions)` and `sample_regions(source_positions, region_ids)` evaluate velocity at those same source coordinates; neither method applies a warp. World-coordinate transformation belongs to the outer composition.

Volcanic relief and its configuration live together in `elevation/volcanism.py`; the generic rod primitive remains in `field/rod.py`. Geology supplies inputs to elevation without importing elevation modules. Definitions are ordered so volcanic annotations use ordinary runtime imports, without `TYPE_CHECKING` guards or quoted forward references.

### Stages

1. Generate independent Cartesian seed clouds for the tectonic and crust partitions. The crust partition labels its seeds continental or oceanic; it is independent of the tectonic partition.
2. Give each tectonic seed an Euler rotation and evaluate its local rotational velocity with `ω × p` in 3D source space.
3. Derive smooth regional memberships from Voronoi seed-distance comparisons. Pairwise regional overlap supplies boundary orientation and the two region identities without clipped boundary meshes.
4. Resolve relative motion into independent convergence, divergence, and shear channels. The opening split uses SciPy smooth minimum/maximum functions, preserving the signed opening difference while allowing a narrow neutral transition. Tangential magnitude is regularized with exact zero at zero tangential motion. Crust influence and the seed-derived polarity field remain separate inputs to later response profiles.
5. Evaluate continuous coastal, collision/subduction, rift/ridge, transform, shear, and volcanic relief profiles. Volcanism combines subduction arcs with independently seeded static hotspot rods. These components remain named and independently sampleable before they are composed.
6. Add general terrain variation as the final world-coordinate contribution. The complete elevation is still a continuous field; mesh vertices only sample it.
7. Derive land height, water depth, slope, local relief, and roughness in the separate surface stage. These measurements do not feed back into elevation.

The engine produces a static procedural snapshot; plate rotation is a kinematic input, not a time simulation. The current continuous pipeline does not include eruption/activity states, meteor impacts, climate, hydrology, or erosion.

### Noise primitive

OpenSimplex2S is the standard coherent-noise primitive. Production noise is composed through `field/noise.py`: scalar fBm, normalized values, vector channels, and parameter modulation share that backend. Octave layering and the invertible shear warp remain separate operations, rather than alternative noise algorithms.

### Differentiability

The source profile algebra uses piecewise closed-form functions with continuous first derivatives (`C1`) for valid positive smoothing scales, ridge sharpness at least one, and rod profile power at least two. Analytic first-order derivatives are propagated through the continuous elevation composition. This does not make the field globally real analytic: compact supports are piecewise smooth, and floating-point evaluations remain finite precision.

- Collision crests and distributed ridge-detail peaks flatten smoothly at their centers; continental rift shoulders also have a zero center slope.
- Shear uses a zero-preserving regularized norm. Oblique transform and pure-shear response denominators use a smooth normal magnitude, so zero relative motion is nonsingular. At small motions this intentionally replaces the former exact shear partition and scale homogeneity with smooth responses. `TectonicResponseConfig.motion_smoothing_width` owns the positive response-smoothing scale and passes it explicitly through both independent and combined relief paths.
- Compact smoothstep and rod supports are retained: their first derivatives join zero continuously. They need not be replaced by infinite-tail smooth extrema.
- Volcanic strengths use a quadratic smooth upper cap instead of hard clipping. Raw arc and hotspot contributions are combined before each final output is capped exactly once; concentration attenuates the raw arc before the strength cap. The independent intraplate diagnostic caps its own output and is not fed back into this composition. `VolcanismConfig.saturation_half_width` defaults to `0.05`: the cap leaves inputs through `0.95` unchanged and reaches the exact ceiling of one at `1.05`. The amplitude knee is dimensionless, independent of spatial widths and planet radius.

Engine pins [our PyFastNoiseLite fork](https://github.com/CrashHermit/PyFastNoiseLite/tree/analytic-opensimplex2s-gradients) version `0.0.8.dev1` to commit `efc5d451034912a2642c8801cffd177eb59f6e85`, which pins [our native FastNoiseLite fork](https://github.com/CrashHermit/FastNoiseLite/tree/analytic-opensimplex2s-gradients) to `83e907f5626a60b63f051c00e28c68188c4cf2dc`. The raw 3D OpenSimplex2S API provides analytic Cartesian gradients through `get_open_simplex2s_with_gradient(x, y, z)` and `gen_open_simplex2s_with_gradient_from_coords(coords)`. The latter accepts float32 XYZ rows `(3, N)` and returns values `(N,)` plus gradients `(N, 3)`, including the configured frequency and internal orientation.

The corrected 3D OpenSimplex2S kernel includes every positive compact-support corner contribution. Four opposite-corner pairs on each of two cubic lattices give eight provably sufficient candidates; pair switches occur only where both contributions are zero. This removes the inherited corner-selection discontinuities. The underlying contributions and their first derivatives join continuously in real arithmetic; finite-precision coordinate quantization and rounding remain. Seed hashing, gradient tables and normalization are retained, but noise values and generated geography can change. Two-dimensional OpenSimplex2S and the other noise algorithms are unchanged.

`field/differential.py` defines immutable `ScalarSample(values, gradients)` with shapes `(N,)` and `(N, 3)`, and `VectorSample(values, jacobians)` with shapes `(N, 3)` and `(N, output_axis, input_axis)`. Query methods take arbitrary XYZ positions; they do not require a region ID, mesh, resolution, or probing neighborhood.

- Noise fBm, normalized noise, parameter multipliers, and vector channels expose analytic derivatives from the pinned noise backend. The forward and inverse shear transforms expose exact chain-rule Jacobians; inverse shears run in reverse order.
- Regional memberships, pair overlap, Euler motion, material and polarity, coastal relief, all tectonic responses, volcanic rods/arcs, and final world-coordinate terrain variation propagate their analytic derivatives. `SourceElevationField.sample_source_with_gradient()` keeps the named contributions accessible and reuses same-query geological inputs.
- For the world-to-source coordinate map, scalar gradients and normals use the transposed Jacobian; normals are then normalized. Source vectors use an inverse-Jacobian solve, not the same transformation as normals. `geometry/differential.py` supplies forward and reverse transport for vectors, covectors, and normals.
- `WorldField.region_velocity.sample()` and `sample_boundary_vectors()` expose transported world-space motion and oriented pair normals. Construction C still calculates geological interactions in unwarped source space and warps the completed scalar fields; these accessors do not change that model.
- `WorldField.elevation.sample_with_gradient()` returns final radius-fraction elevation and its Cartesian gradient. `sample_elevation_meters_with_gradient()` scales both by the requested radius. Surface point slope and radial-surface normals use these gradients; local relief and roughness remain finite-footprint statistics.

Value-only sampling does not calculate derivatives. Custom injected value-only functions remain usable for value queries; derivative queries require corresponding analytic callbacks rather than silently probing neighboring positions. These APIs expose first-order scalar gradients and coordinate Jacobians, not Hessians or spatial derivatives of already transported vector/normal fields.

Inputs, outputs, and paired derivative callbacks are trusted. Field construction and derivative sampling do not add validation, retries, numerical fallback, or repair logic.

Float32 noise coordinates, particularly the large per-octave offsets, limit finite-difference diagnostics at tiny step sizes. Analytic gradients describe the underlying smooth noise composition; they do not differentiate floating-point rounding. Categorical ownership, ownership-selected velocity jumps, and diagnostic extrema are not globally differentiable terrain inputs.


## Configuration and APIs

Configuration is separated from results:

- `WorldgenConfig` controls seed, mesh subdivision frequency, planet radius, warp, geology, elevation, and surface measurements.
- `GeologyConfig` controls plate seeds and rotation speeds, the smooth opening-motion transition, crust seeds and transition width, crust density variation, material blending, and subduction preference.
- `--opening-smoothing-width` sets the positive SciPy smooth-extrema transition for convergence/divergence. The default `0.01` creates a narrow neutral blend; the former width-zero hard split has been removed. `GeologyConfig.boundary_motion.shear_smoothing` independently controls tangent-magnitude regularization in motion units.
- `config.elevation.tectonic.motion_smoothing_width` controls transform/shear response regularization in motion units, defaulting to `0.01`. It is independent of the geological tangent-magnitude smoothing above. Lower-level fault response functions require an explicit `smoothing` argument rather than choosing a hidden default.
- `TectonicResponseConfig` owns the subduction arc and trench defaults. The lower-level `blend_subduction_orientations()` helper requires an explicit profile configuration and both amplitude multipliers; standalone calls do not choose a second set of geological defaults.
- `PlanetConfig.radius_m` sets the output scale. Elevation heights are configured as percentages of radius; source-space profile widths use unit-radius fractions or percentages as named by their configuration field. Surface footprint is a percentage of circumference.
- The CLI builds one `WorldgenConfig`, derives generation defaults from it, and applies overrides with `replace()` so nested noise and unrelated settings are retained. The default `--frequency` is therefore `40`, matching the central configuration rather than the former CLI-only value `20`. Display-only settings such as `--field-frequency` remain viewer choices.

Example arbitrary-point query:

```python
import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field

config = WorldgenConfig(seed=2026)
field = generate_world_field(config)
points = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
sample = field.sample_world(points)
continental_weight = sample.geology.continental_weight
height = field.sample_elevation_meters_with_gradient(
    points, radius_m=config.planet.radius_m
)
elevation_m = height.values
gradient_xyz = height.gradients  # meters per unit Cartesian coordinate
divergence = field.divergence.sample_with_gradient(points)
coordinates = field.warp.sample_with_jacobian(points)
original_points = field.warp.inverse(coordinates.values)
region_velocities = field.region_velocity.sample(points)
boundary_pairs = field.sample_boundary_vectors(points)
```

The array fields on `WorldSample.geology` and `WorldSample.elevation` are read-only and aligned with the query positions. Geology exposes `plate_ids`, `crust_region_ids`, `continental_mask`, continuous `continental_weight`, subduction-preference strength, region overlap, convergence, divergence, and shear. Elevation exposes coastal, convergent, divergent, transform, shear, total tectonic, volcanic potential/strength/relief, terrain-variation, and total-elevation contributions.

`BoundaryResponseField` callbacks return one complete contribution per active region pair, including the desired overlap weighting. The field only sums those contributions into query positions; it does not multiply by influence again.

`GeneratedWorld` holds the sampled mesh artifact (`mesh`, `geology`, `elevation`, and `surface`) alongside the reusable `field` and `surface_field`. The continuous field can therefore be sampled again at finer or irregular coordinates without regenerating the seed layout.

## Visualization

Run the interactive viewer:

```bash
uv run python -m src.worldgen --seed 2026 --frequency 20 --layer elevation
```

By default, scalar layers sample the continuous field on the dense display mesh. Use `--hex-samples` to display the same value sampled only at the generated hex centers. The viewer includes clickable layer selection, continuous/hex sampling, hex-edge, water, and terrain-relief controls; changing a view does not regenerate the world.

Display radial relief with the water surface:

```bash
uv run python -m src.worldgen --layer elevation --water \
  --vertical-exaggeration 25 --no-hex-edges
```

`--water` shows a sea-level surface and enables radial terrain relief. `--sea-level` remains an alias.

Render a screenshot without opening a window:

```bash
uv run python -m src.worldgen --frequency 20 --field-frequency 80 \
  --layer elevation --water --vertical-exaggeration 25 \
  --off-screen --screenshot /tmp/world-water.png
```

`--frequency` sets generated hex resolution; `--field-frequency` sets the dense visualization mesh resolution. `--radius-m` controls the physical planet radius. `--elevation-min` and `--elevation-max` set color limits in meters without changing the generated field. `--rotation-gif PATH` renders the selected layer as an off-screen rotating GIF. Run `uv run python -m src.worldgen --help` for the full configuration and display options. Layer names are defined in `src/worldgen/render/layers.py`.

Subduction trench depth is scaled independently from the convergence field and overriding arc. The default `--subduction-trench-depth-multiplier 0.5` halves the previous trench depth without changing the arc or the shared interaction width; use `1.0` to render the previous trench strength.

Inspect volcanic relief with a denser display mesh and an explicitly stronger preview amplitude:

```bash
uv run python -m src.worldgen --seed 123 --plate-count 64 \
  --frequency 40 --field-frequency 240 \
  --plate-transition-half-width-percent 25 --terrain-variation-percent 0.012 \
  --volcanic-height-percent 0.0314 --terrain-relief \
  --vertical-exaggeration 25 --no-hex-edges
```

Use the `volcanic-potential`, `volcanic-strength`, and `volcanic-relief` layers to isolate contributions. The default maximum volcanic height remains `0.0047%` of radius; the preview above uses `0.0314%`.

`--hotspot-count` controls the number of independent rods, `--hotspot-width-min-percent` and `--hotspot-width-max-percent` their radial support, and `--hotspot-length-percent` their finite origin-to-tip length. Widths and lengths are percentages of the source reference unit mapped to planet radius, not distances along the warped surface. `--hotspot-noise-strength` controls height attenuation only. Python configuration separately exposes width-noise strength, taper, profile power, and amplitude range.

The reusable `field.rod.RodScalarField` evaluates static one-sided rods from the origin, with smooth radial and axial support and optional injected width/length/height multipliers. Gaussian direction seeds are independent of plate axes and Voronoi sites; seed magnitude is discarded. `VolcanicField.sample_intraplate(points)` exposes their bounded source-space strength independently of arcs. The rods pass through the existing geological warp exactly once; narrow features can be missed by coarse hex samples. Intraplate strength now scales these sparse mounds rather than broad noise provinces.


Generate the mobile-friendly crust/elevation gallery for seeds 123, 2026, and 31415:

```bash
uv run python experiments/crust_material_gallery.py \
  --output /tmp/crust-material-gallery --frequency 20 \
  --field-frequency 80 --radius-m 6371000
```

The output contains `crust-material.html`, a JSON manifest, and matched field/hex/elevation images. Set `--radius-m` to compare another planet scale; the configured percentages remain unchanged.

## Verification

```bash
uv run pytest --import-mode=importlib --assert=plain test/worldgen
uv run ruff check src/worldgen test/worldgen experiments
uv run ruff format --check src/worldgen test/worldgen experiments
```
