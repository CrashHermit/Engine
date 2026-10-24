# World generation

The world is defined by continuous fields in Cartesian 3D. The globe and hex mesh are sampling and presentation surfaces; neither defines the underlying geology.

## Generation model

`generate_world_field(config)` builds a mesh- and planet-radius-independent `WorldField`. `WorldField.sample_world(points)` accepts arbitrary `N × 3` coordinates and returns a `WorldSample` containing named geology, elevation, and climate results. `generate_world(config)` creates an icosphere, samples those fields at its vertices, and derives surface measurements. Each field query is deterministic, batch-independent, and does not mutate NumPy's global random state.

The common coordinate frame is the centered Cartesian cube `[-1, 1]³`. The planet is a sampling surface in that volume. The shared shear warp maps world queries into source coordinates for region ownership, profile distances, and source noise. Before resolving geological interactions, velocities, boundary normals, and polarity-preference vectors are transported into the world frame:

```text
source_position = W(world_position)
world_elevation = (source_relief(source_position) + volcanic_relief(world_position)
                   + impact_relief(world_position) + terrain_variation(world_position))
```

Terrain variation is intentionally sampled in world coordinates after the geological warp. Geometry is not projected onto the sphere during field construction. `WorldField.sample_elevation_meters(points, radius_m=...)` converts the radius-fraction elevation into meters.

`RegionRotationField` owns an unwarped source partition. Both `sample(source_positions)` and `sample_regions(source_positions, region_ids)` evaluate velocity at those same source coordinates; neither method applies a warp. World-coordinate transformation belongs to the outer composition.

For a world point $\mathbf p$, source point $\mathbf q=W(\mathbf p)$, and inverse-map Jacobian $\mathbf K(\mathbf q)=\partial W^{-1}/\partial\mathbf q$, the compared inputs are

$$
\mathbf v_i^{\text{world}}(\mathbf p)
=\mathbf K(\mathbf q)(\boldsymbol\omega_i\times\mathbf q),
\qquad
\mathbf n^{\text{world}}(\mathbf p)
=\frac{\mathbf K(\mathbf q)^{-T}\mathbf n^{\text{source}}}
{\left\lVert\mathbf K(\mathbf q)^{-T}\mathbf n^{\text{source}}\right\rVert}.
$$

Both sides' velocities and the ordered pair normal use the same transport. Opening/closing signs are preserved, while normal-motion magnitude and shear can change. These transported velocity fields are no longer rigid rotations in world coordinates; the source Euler model remains unchanged. This is a static procedural input, not movement of the regions.

`GeologyField.sample_source(q)` and `SourceReliefField.sample_source(q)` remain source-parameterized queries, but their geological motion inputs are world-oriented. Their gradients are with respect to `q`; the final world composition pulls them back through `W`. Source plane distances, overlap supports, profile widths, and crust scalar values keep their existing source-coordinate meaning, not exact warped Euclidean distances.

Volcanic relief and its configuration live together in `relief/volcanism.py`; the generic rod primitive remains in `field/rod.py`. Geology supplies inputs to relief without importing relief modules. Definitions are ordered so volcanic annotations use ordinary runtime imports, without `TYPE_CHECKING` guards or quoted forward references.

Relief names the shape-producing mechanisms; elevation names the completed height
output. Configure mechanisms through `WorldgenConfig.relief` (`ReliefConfig`).
`WorldField.source_relief` exposes the source-space composition, while
`WorldField.elevation` (`ElevationField`) adds world-space volcanism, impacts, and
terrain variation. The viewer's `elevation` layer and meter-sampling APIs retain
their height-oriented names.

Geology supplies `SourceReliefInputs` and `SourceReliefGradientInputs`: dense
continental weights, sparse query indices, and interpreted tectonic context.
`GeologySample.to_relief_inputs()` and its gradient counterpart project existing
arrays without copying. Source relief and volcanic suitability receive typed
sampling callbacks rather than complete geology objects. World sampling passes
the projection from its existing geology query into the elevation composition,
preserving shared work and the original source-coordinate gradient semantics.

Each process defines its own configuration beside its implementation. Domain
`config.py` modules compose those settings into `GeologyConfig`, `ReliefConfig`,
and `ClimateConfig`; `WorldgenConfig` composes the domains. Shared tectonic
width/height settings live in `relief/profile_config.py` as `ReliefProfileConfig`,
and the plate partition/motion composite lives in `geology/plate_config.py`.
Import leaf settings from their process modules, not the domain aggregators.

Tectonic numerical work follows the same ownership pattern for values and
gradients: `relief/collision.py`, `subduction.py`, `divergence.py`, and
`fault.py` own their scalar profiles and compiled per-record evaluators.
These evaluators accept numerical arrays and parameters, without geological
context or configuration objects. `relief/tectonic_response.py` composes
their results, blends collision/subduction and rift/ridge by material, and
applies regional overlap once, including the analytic product-rule terms.
Field sampling and the final sparse reduction remain outside the profile
evaluators.

Names distinguish the mathematical roles: `*_profile` functions describe
normalized shapes, while `*_relief` evaluators scale those shapes into elevation
contributions. The `*_response_with_gradient` / `*_responses_with_gradient`
evaluators additionally include motion saturation and procedural detail, but
not material mixing or overlap weighting. Their returned Cartesian gradients
differentiate those same responses. `TectonicReliefSample` and
`TectonicReliefGradientSample` name the composed elevation contributions,
not the convergence/divergence/shear motion fields.

### Composition ownership

World orchestration constructs dependencies, shares query intermediates, and assembles sampled artifacts. Domain components own their interpretation and profile laws; generic field and geometry tools own reusable mathematical operations. Domain folders are not restricted to wiring.

`relief/composition.py:ElevationField` owns the completed elevation: warped coastal/tectonic source relief plus world-space volcanism, impacts, and variation. It exposes `sample()`, `sample_with_gradient()`, and `sample_components()`. `WorldField.elevation` is this composed field. World sampling delegates component calculation to it, passing already-sampled source coordinates and relief inputs so the refactor does not repeat geological queries. The source gradient is pulled back through the warp Jacobian before adding world-space gradients.

Continental response and subduction-preference derivatives live beside their value laws in geology; tectonic context composes them with input gradients. Coastal, terrain-noise, and tectonic gradient paths reuse intermediate values instead of evaluating a second scalar path. Scalar-only queries still avoid derivative work. Coastal and tectonic samplers require their analytic-gradient callbacks explicitly rather than advertising optional dependencies that gradient methods invoke unconditionally.

`geometry/vector.py` owns regularized vector normalization and its input-vector Jacobian. Zonal wind composes that operation with rotational velocity and the circulation coefficient; climate retains its direction, speed, and calm-region policy. The refactor preserves scalar worlds, with only floating-point-scale changes in analytical derivatives and derived slope measurements.


### Stages

1. Generate independent Cartesian seed clouds for the tectonic and crust partitions. The crust partition labels its seeds continental or oceanic; it is independent of the tectonic partition.
2. Give each tectonic seed an Euler rotation and evaluate its local rotational velocity at the source query point in 3D.
3. Derive smooth regional memberships from Voronoi seed-distance comparisons. Pairwise regional overlap supplies boundary orientation and the two region identities without clipped boundary meshes.
4. Transport the selected region velocities, pair normals, and polarity-preference vectors into the world frame, then resolve relative motion into independent convergence, divergence, and shear channels. The opening split uses SciPy smooth minimum/maximum functions, preserving the signed opening difference while allowing a narrow neutral transition. Tangential magnitude is regularized with exact zero at zero tangential motion. Crust influence and transported preference remain separate inputs to later response profiles.
5. Evaluate continuous coastal, collision/subduction, rift/ridge, transform, and shear relief in the warped geological composition. These components remain named and independently sampleable.
6. Add world-space volcanic rods, meteor impacts, and finally general terrain variation. Volcanic placement uses independent hotspot suitability and warped tectonic suitability, but the resulting mound shapes are never warped. The complete elevation is continuous; mesh vertices only sample it.
7. Derive land height, water depth, slope, local relief, and roughness in the separate surface stage. These measurements do not feed back into elevation.

The engine produces a static procedural snapshot; plate rotation is a kinematic input, not a time simulation. The current continuous pipeline includes prevailing zonal circulation and a latitude-temperature baseline, but not eruption/activity states, precipitation, hydrology, or erosion.

### Planetary axis and prevailing circulation

`PlanetConfig.rotation_axis` defines planetary north independently of plate Euler poles. It defaults to `(0, 0, 1)`; the generic `AxialCoordinateField` normalizes this nonzero direction once. Its scalar coordinate is the dot product of axis and position. On the unit sphere this equals sine latitude; elsewhere it remains an unbounded linear Cartesian coordinate, including at the origin.

`climate/circulation.py` composes that coordinate with a sinusoidal five-zone direction-and-strength field and the generic `RotationField`. For axial coordinate $s=\mathbf a\cdot\mathbf p$, the signed coefficient is

$$
b(\mathbf p)=-\text{cos}(2\pi s^2),
\qquad
\nabla b(\mathbf p)=4\pi s\,\text{sin}(2\pi s^2)\,\mathbf a.
$$

On the unit sphere, tropics and polar regions flow westward; the two middle-latitude zones flow eastward. Reversals occur at ±30° and ±60°, with coefficient extrema at the equator, ±45°, and the poles. Strength varies throughout each band instead of forming plateaus with narrow transitions. The squared axial coordinate supplies north/south symmetry without an absolute-value kink. These are volumetric fields, with no surface projection or geological warp; beyond the unit sphere the wave continues oscillating rather than clamping to a polar band. The scalar wave is smooth to all derivative orders in real arithmetic; sampling exposes analytic first derivatives.

`config.climate.circulation` owns `base_speed_m_s=10` and `axis_calm_radius_percent=5` (percentage of the unit reference radius). The former boundary-angle and transition-width controls have been removed: the wave determines their relationship. The rotational cross product supplies direction, not a physical planetary surface speed. Smooth normalization approaches unit direction away from the axis and goes calmly to zero on the axis; the wave coefficient and reference speed then determine the wind. Wind speed is in m/s, not a fraction of planet radius.

`WorldField.climate.circulation.axis`, `.bands`, and `.wind` remain independently sampleable. Axis/band queries expose `sample_with_gradient()`; wind exposes `sample_with_jacobian()`, all analytically evaluated. `.circulation.sample(points)` returns immutable `axial_coordinate`, `band_strength`, and `wind_vectors_m_s` arrays; the same quantities are available through `WorldSample.climate.circulation` and `GeneratedWorld.climate.circulation`. This is a prevailing-wind component, not yet a full climate model: no meridional flow, seasons, terrain steering, or moisture transport.

```bash
uv run python -m src.worldgen --frequency 20 --field-frequency 100 \
  --layer wind-vectors --no-hex-edges
```

Use **Layers → Climate** to switch between circulation direction, wind vectors, wind speed, and axial coordinate. Blue bands are westward; red bands are eastward. Arrows are display-decimated only. `--rotation-axis 0 1 1` tilts the entire circulation pattern; `--wind-speed-m-s 20` changes its reference speed without altering geology or elevation.

### Latitude temperature baseline

`climate/temperature.py` owns `LatitudeTemperatureField`. It reuses the planetary axial coordinate $s=\mathbf a\cdot\mathbf p$ without depending on wind strength:

$$
T(\mathbf p)=T_{\text{equator}}-\Delta T\,s^2,
\qquad
\Delta T=T_{\text{equator}}-T_{\text{pole}},
\qquad
\nabla T(\mathbf p)=-2\Delta T\,s\,\mathbf a.
$$

`config.climate.temperature` owns `equator_temperature_c=30` and `pole_temperature_c=-20`. These are configurable procedural Celsius baselines, not a physical heat-balance simulation. The quadratic is equivalent to cosine-squared latitude on the unit sphere: both hemispheres match, the equator has a smooth maximum, and the poles reach the configured polar value. It remains polynomial throughout Cartesian space, with no position normalization, clamping, geological warp, or equatorial seam. Beyond unit axial distance its values extrapolate past the polar temperature rather than staying bounded.

`WorldField.climate.temperature.sample(points)` returns temperatures in Celsius; `.sample_with_gradient(points)` returns a `ScalarSample` whose Cartesian gradients are Celsius per unit coordinate. `climate/field.py` composes temperature with circulation and shares each batch's axial values. `WorldSample.climate` and `GeneratedWorld.climate` expose the independently named `temperature_c` and `circulation` results. The former top-level `.circulation` fields have been replaced by `.climate.circulation`.

No elevation cooling, ocean-temperature response, seasons, or regional temperature noise is included yet. Temperature does not modify geology, elevation, or circulation, and its Celsius values do not scale with planet radius.

```bash
uv run python -m src.worldgen --frequency 20 --field-frequency 100 \
  --layer temperature --no-hex-edges
```

**Layers → Climate → Temperature** shows the baseline. `--equator-temperature-c 35 --pole-temperature-c -25` changes its endpoints; `--rotation-axis 0 1 1` tilts the shared circulation and temperature axis.



### Tectonic motion-to-relief response

Relief amplitudes use a smooth bounded response rather than multiplying height directly by arbitrarily strong transported motion:

$$
r(m;\sigma)=\frac{m}{\sqrt{m^2+\sigma^2}},
\qquad
\frac{\partial r}{\partial m}
=\frac{\sigma^2}{(m^2+\sigma^2)^{3/2}}.
$$

`config.relief.tectonic.motion_response_scale` supplies the positive motion scale \(\sigma\), defaulting to `1.0`. This is in motion units, not a percentage of radius or a spatial width. Larger scales weaken the response at a given motion strength; smaller scales approach saturation earlier. At \(m=\sigma\), the response is \(1/\sqrt{2}\); near zero it is approximately \(m/\sigma\).

Convergence controls collision/subduction amplitude, divergence controls rift/ridge amplitude, and the raw obliquity decomposition supplies signed transform and nonnegative shear amplitudes. Each amplitude is saturated once, before profile/detail/overlap modulation. Raw velocities, opening, convergence, divergence, shear, material interpretation, volcanic placement, and all spatial widths are unchanged. Analytic gradients include the response derivative in both independent and combined relief paths.

Only the motion multiplier is bounded. Configured profile shapes, crest/detail amplification, and overlapping contributions can still combine above a single profile's reference height; final elevation is not clamped. The separate `motion_smoothing_width` still controls the regularized transform/shear decomposition, not this amplitude response.

```bash
uv run python -m src.worldgen --seed 123 --frequency 20 \
  --field-frequency 160 --layer elevation --terrain-relief --water \
  --tectonic-motion-response-scale 1 --vertical-exaggeration 25
```


### Noise primitive

OpenSimplex2S is the standard coherent-noise primitive. Production noise is composed through `field/noise.py`: scalar fBm, normalized values, vector channels, and parameter modulation share that backend. Octave layering and the invertible shear warp remain separate operations, rather than alternative noise algorithms.

### Differentiability

The source profile algebra uses piecewise closed-form functions with continuous first derivatives (`C1`) for valid positive smoothing scales, ridge sharpness at least one, and rod profile power at least two. Analytic first-order derivatives are propagated through the continuous elevation composition. This does not make the field globally real analytic: compact supports are piecewise smooth, and floating-point evaluations remain finite precision.

- Collision crests and distributed ridge-detail peaks flatten smoothly at their centers; continental rift shoulders also have a zero center slope.
- Shear uses a zero-preserving regularized norm. Oblique transform and pure-shear response denominators use a smooth normal magnitude, so zero relative motion is nonsingular. At small motions this intentionally replaces the former exact shear partition and scale homogeneity with smooth responses. `TectonicResponseConfig.motion_smoothing_width` owns the positive response-smoothing scale and passes it explicitly through both independent and combined relief paths.
- Compact smoothstep and rod supports are retained: their first derivatives join zero continuously. They need not be replaced by infinite-tail smooth extrema.
- Volcanic rod strengths use a quadratic smooth upper cap instead of hard clipping. Hotspot and tectonic rod contributions are added before the combined output is capped exactly once; placement suitability is not multiplied into queried mound shapes. The independent intraplate diagnostic caps its own output and is not fed back into this composition. `VolcanismConfig.saturation_half_width` defaults to `0.05`: the cap leaves inputs through `0.95` unchanged and reaches the exact ceiling of one at `1.05`. The amplitude knee is dimensionless, independent of spatial widths and planet radius.

Engine pins [our PyFastNoiseLite fork](https://github.com/CrashHermit/PyFastNoiseLite/tree/analytic-opensimplex2s-gradients) version `0.0.8.dev2` to commit `de35cb717f52d5955519ea27a046876e7fbe5a31`, which pins [our native FastNoiseLite fork](https://github.com/CrashHermit/FastNoiseLite/tree/analytic-opensimplex2s-gradients) to `3ecd97e8f6c7627d1ad7b0fc2b4aec617f82894d`. The raw 3D OpenSimplex2S API provides analytic Cartesian gradients through `get_open_simplex2s_with_gradient(x, y, z)` and `gen_open_simplex2s_with_gradient_from_coords(coords)`. The batch API accepts float32 XYZ rows `(3, N)` and returns values `(N,)` plus gradients `(N, 3)`, including configured frequency and internal orientation. The corresponding `get_open_simplex2s_with_hessian()` and `gen_open_simplex2s_with_hessian_from_coords()` additionally return symmetric Cartesian Hessians `(N, 3, 3)`.

The corrected 3D OpenSimplex2S kernel includes every positive compact-support corner contribution. Four opposite-corner pairs on each of two cubic lattices give eight provably sufficient candidates; pair switches occur only where both contributions are zero. This previously removed the inherited corner-selection discontinuities. Contributions, gradients, and Hessians join continuously in real arithmetic; finite-precision coordinate quantization and rounding remain. The Hessian addition preserves existing scalar values and gradients. Two-dimensional OpenSimplex2S and the other noise algorithms are unchanged.

`field/differential.py` defines immutable `ScalarSample(values, gradients)` with shapes `(N,)` and `(N, 3)`, and `VectorSample(values, jacobians)` with shapes `(N, 3)` and `(N, output_axis, input_axis)`. Query methods take arbitrary XYZ positions; they do not require a region ID, mesh, resolution, or probing neighborhood.
`ScalarHessianSample` adds Hessians with shape `(N, 3, 3)`; `VectorHessianSample` adds map Hessians with shape `(N, output_axis, input_axis, input_axis)`. These second-order APIs are available for noise and coordinate warps. Final elevation still exposes first-order gradients.

- Noise fBm, normalized noise, and parameter multipliers expose analytic gradients and Hessians from the pinned noise backend. The forward and inverse shear transforms expose chain-rule Jacobians and Hessians; inverse shears run in reverse order.
- Regional memberships, pair overlap, Euler motion, material and polarity, coastal relief, tectonic responses, world-space volcanic rods and impacts, and final terrain variation propagate their analytic derivatives. `SourceReliefField.sample_source_with_gradient()` contains coastal and tectonic contributions only; `WorldField` adds the world-space components and their gradients.
- For the world-to-source coordinate map, scalar gradients and normals use the transposed Jacobian; normals are then normalized. Source vectors use an inverse-Jacobian solve, not the same transformation as normals. `geometry/differential.py` supplies forward and reverse transport for vectors, covectors, and normals.
- `TransportedBoundaryVectorField` composes source pair selection with vector/normal transport. Those same transported inputs drive generated geological interactions and are exposed by `WorldField.region_velocity.sample()` and `sample_boundary_vectors()`. `region_velocity.sample_with_jacobian()` also exposes world-coordinate velocity derivatives.
- `WorldField.elevation.sample_with_gradient()` returns final radius-fraction elevation and its Cartesian gradient. `sample_elevation_meters_with_gradient()` scales both by the requested radius. Surface point slope and radial-surface normals use these gradients; local relief and roughness remain finite-footprint statistics.

Kinematic value queries evaluate the warp Jacobians required for transport, but do not calculate Hessians. Gradient queries additionally use analytic warp Hessians to differentiate changing transported velocities and normals, including the normal-derivative term in opening, shear, and polarity. No numerical neighborhood probing is used. Custom injected value-only functions remain usable for value queries; derivative queries assume corresponding analytic callbacks are supplied. `PushforwardVectorField` changes vector components while retaining source query coordinates; `ReparameterizedVectorField` composes coordinates without transporting those components a second time.

Inputs, outputs, and paired derivative callbacks are trusted. Field construction and derivative sampling do not add validation, retries, numerical fallback, or repair logic.

Float32 noise coordinates, particularly the large per-octave offsets, limit finite-difference diagnostics at tiny step sizes. Analytic gradients describe the underlying smooth noise composition; they do not differentiate floating-point rounding. Categorical ownership, ownership-selected velocity jumps, and diagnostic extrema are not globally differentiable terrain inputs.


## Configuration and APIs

Configuration is separated from results:

- `WorldgenConfig` controls seed, mesh subdivision frequency, planetary settings, warp, geology, relief, climate, and surface measurements.
- `GeologyConfig` controls plate seeds and rotation speeds, the smooth opening-motion transition, crust seeds and transition width, crust density variation, material blending, and subduction preference.
- `--opening-smoothing-width` sets the positive SciPy smooth-extrema transition for convergence/divergence. The default `0.01` creates a narrow neutral blend; the former width-zero hard split has been removed. `GeologyConfig.boundary_motion.shear_smoothing` independently controls tangent-magnitude regularization in motion units.
- `config.relief.tectonic.motion_smoothing_width` controls transform/shear response regularization in motion units, defaulting to `0.01`. It is independent of the geological tangent-magnitude smoothing above. Lower-level fault response functions require an explicit `smoothing` argument rather than choosing a hidden default.
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

The array fields on `WorldSample.geology` and `WorldSample.elevation` are read-only and aligned with the query positions. Geology exposes `plate_ids`, `crust_region_ids`, `continental_mask`, continuous `continental_weight`, subduction-preference strength, region overlap, convergence, divergence, and shear. Elevation exposes coastal, convergent, divergent, transform, shear, total tectonic, volcanic strength/relief, impact relief, terrain variation, and total elevation. The old volcanic-potential diagnostic was removed: without the old concentration gate it duplicated volcanic strength.

`BoundaryResponseField` callbacks return one complete contribution per active region pair, including the desired overlap weighting. The field only sums those contributions into query positions; it does not multiply by influence again.

`GeneratedWorld` holds the sampled mesh artifact (`mesh`, `geology`, `elevation`, `surface`, and `climate`) alongside the reusable `field` and `surface_field`. The continuous field can therefore be sampled again at finer or irregular coordinates without regenerating the seed layout.

## Visualization

Run the interactive viewer:

```bash
uv run python -m src.worldgen --seed 2026 --frequency 20 --layer elevation
```

The desktop viewer uses a native Qt window (`PySide6` + `pyvistaqt`), with no buttons or sliders drawn over the globe:

- **Layers** groups diagnostics into Geography, Tectonic relief, Motion, Partitions and material, Volcanism, Surface, and Climate. Exactly one layer is selected at a time.
- **View** toggles terrain relief, water, hex outlines, continuous-field sampling, and the dockable Settings panel. **Reset camera** (`Home`) fits the globe.
- **Settings → Display** adjusts vertical exaggeration using a numeric input or slider. These changes do not regenerate the world.
- **Settings → Generation** changes plate count. Click **Rebuild world**, or use **Generation → Rebuild world** (`Ctrl+R`), to apply it. Merely editing the count does not start expensive generation.
- **File → Save screenshot** (`Ctrl+S`) exports the globe without the surrounding window controls.

By default, scalar layers sample the continuous field on the dense display mesh. Use `--hex-samples`, or disable **View → Continuous field**, to use generated hex samples. Categorical and surface-measurement layers always use hex samples.

Rebuilding retains the seed, other generation settings, selected layer, camera,
and display toggles. Generation, display-update, and total elapsed seconds appear
in the Settings panel and status bar and are printed to the terminal.
The rebuild remains synchronous, with a busy cursor while it runs. Automatic
elevation color limits are recalculated; explicit CLI color limits remain fixed.

`render/viewer.py` owns the rendering scene and accepts an injected plotter;
`render/window.py` owns native menus and controls; `render/rebuild.py` owns
toolkit-independent regeneration and timing. Off-screen screenshots and rotation
GIFs use the scene directly without creating a Qt application.

Try it at a known generation and display resolution:

```bash
uv run python -m src.worldgen --seed 123 --frequency 20 --field-frequency 120 \
  --layer elevation --water --vertical-exaggeration 25 --no-hex-edges
```

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

Use `volcanic-strength` and `volcanic-relief` to inspect the placed mounds. The default maximum height remains `0.0047%` of radius; the preview above uses `0.0314%`.

`config.relief.volcanism` configures two independent populations: `hotspot_count=48` and `tectonic_count=48`. Both use `candidate_count=4096` unit-direction candidates. Hotspot placement is biased by independent coherent noise; tectonic placement favors the overriding-side subduction-arc response and a separately weighted divergent contribution (`divergence_strength=0.5`), suppressed by continental-collision influence. There is no shear-based volcanic term; the existing smooth normal-motion split retains its small neutral baseline. Selection uses weights raised to `hotspot_bias=2` or `tectonic_bias=2`: increasing a bias concentrates placement, not mound height. This is probabilistic concentration, not guaranteed chains or clusters. Candidate resolution is fixed and configurable; there are no retries or fallback placements.

CLI controls are `--hotspot-count`, `--tectonic-volcano-count`, `--volcanic-candidate-count`, `--hotspot-placement-bias`, `--tectonic-placement-bias`, and `--volcanic-height-percent`. Python configuration separately controls each population's `*_width_min_percent`, `*_width_max_percent`, `*_length_percent`, and amplitude range. Spatial and elevation percentages scale with planet radius. Set either count to zero without changing the other population's random stream.

`field.seeds.select_weighted_seeds(candidates, weights, count, rng=...)` selects without replacement from trusted nonnegative weights and knows nothing about fields or volcanism. Callers generate candidates, normalize direction seeds before sampling suitability, then compose selection with any scalar field. `VolcanicField.hotspot_suitability()` and `tectonic_suitability()` expose world-coordinate placement values and have matching `_with_gradient()` methods. The tectonic guide queries warped geology; selection happens once during construction.

`WorldField.volcanism` owns `hotspots` and `tectonic_rods`, both reusable `RodScalarField` instances with fixed per-rod dimensions and amplitudes. Elevation queries sample these rods directly at world XYZ without suitability queries, shape-noise modulation, or geological warping. `sample_intraplate(points)` exposes the bounded hotspot contribution. The old broad volcanic-arc relief and concentration/noise-gate controls were replaced, not retained as alternate paths. Fine display meshes are needed to resolve small mounds.

### Meteor impacts

`relief/impact.py` colocates `ImpactConfig`, the crater profile, and the independently sampleable `ImpactField`. Origin-based, one-sided rods use the same direction-seed and rod-coordinate tools as volcanic placement, but are evaluated in **world coordinates after the geological warp**, not stretched with the source geology. Each rod contributes a negative bowl and raised annular rim, then returns exactly to zero outside its footprint. Overlapping impacts add. There are no age records, cell masks, separate influence fields, or noise modulation.

`WorldField.impact_relief.sample(points)` returns radius-fraction relief; `sample_with_gradient(points)` returns its analytic Cartesian gradient through the existing `ScalarSample` contract. The radial profile has C2 joins; the shared axial smoothstep taper is C1. Rods extend beyond the unit sampling surface so their tip taper does not suppress the crater. The total elevation and its gradient include impacts before final terrain variation, and `WorldSample.elevation.impact_relief` exposes the sampled contribution separately.

Configure `config.relief.impacts`: `count` defaults to 16; `radius_min_percent` / `radius_max_percent` to 0.8 / 3.0; `depth_min_percent` / `depth_max_percent` to 0.003 / 0.02; `rim_height_min_percent` / `rim_height_max_percent` to 0.0005 / 0.004. These are percentages of planet radius, not hardcoded meter lengths. Radius is the **outer footprint radius**. `rim_width_fraction=0.25` sets the annulus width relative to that radius; `length_percent=180` and `taper_fraction=0.1` control axial support. Set `count=0` to disable impacts without changing any other generation stream.

Inspect the contribution independently, then select `elevation` in the viewer to see the composed result:

```bash
uv run python -m src.worldgen --seed 123 --frequency 20 \
  --field-frequency 160 --layer impact-relief --terrain-relief \
  --vertical-exaggeration 25 --no-hex-edges
```

Small craters can be missed by coarse display meshes; increasing display resolution samples the same field, rather than regenerating impacts.



Generate the mobile-friendly crust/elevation gallery for seeds 123, 2026, and 31415:

```bash
uv run python experiments/crust_material_gallery.py \
  --output /tmp/crust-material-gallery --frequency 20 \
  --field-frequency 80 --radius-m 6371000
```

The output contains `crust-material.html`, a JSON manifest, and matched field/hex/elevation images. Set `--radius-m` to compare another planet scale; the configured percentages remain unchanged.

## CPU field execution

Regional membership values, analytic membership gradients, and sparse overlap extraction parallelize over query positions using Numba. Each query retains the original region-pair arithmetic order; overlap records remain ordered by query, then region pair. This changes execution only, not the continuous field definitions or sampling resolution.

Small queries use serial compiled kernels to avoid thread-launch overhead. Both paths share the same numerical implementation and have separate compiled cache entries. No worker settings belong to geological configuration, and the package does not change process-wide thread counts.

Tectonic relief gradients also use compiled numerical kernels for collision/subduction, rift/ridge, and transform/shear responses. Large batches parallelize over independent region-pair records, not over their final reduction into query totals. Small batches stay serial. Profile equations, value-only evaluation, analytic chain rules, and pair-reduction order remain unchanged; no numerical differentiation is introduced.

Volcanic rod fields use compiled value-only and analytic-gradient kernels. Large workloads parallelize over query positions while each position accumulates rods in their original order. Width, length, and height modifier fields are evaluated once per query batch outside the kernels; no query-by-rod temporary arrays are constructed. Shared rod geometry helpers used by impacts remain available.

Numba chooses the available worker count by default. To limit it, set `NUMBA_NUM_THREADS` before starting Python:

```bash
NUMBA_NUM_THREADS=4 uv run python -m src.worldgen --seed 123 --frequency 20
```

Use `NUMBA_NUM_THREADS=1` for single-worker execution. Worker-count performance depends on the machine and workload; more workers are not always faster. First use of a new kernel signature includes compilation, so compare warmed rebuilds separately from startup.


## Verification

```bash
uv run pytest --import-mode=importlib --assert=plain test/worldgen
uv run ruff check src/worldgen test/worldgen experiments
uv run ruff format --check src/worldgen test/worldgen experiments
```
