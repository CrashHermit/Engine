# Phase 2 — Climate: Insolation, Temperature, Wind, Moisture

*Prerequisite: Phase 1 (real terrain in the viewer). Shorter and gentler than
Phase 1 — mostly array expressions, one small simulation loop at the end.*

**What Phase 2 delivers:** `temperature`, `precipitation`, and wind fields that
are *caused by* the terrain and the world's authored energy pattern — wet
windward coasts, dry interiors, rain shadows behind your mountain ranges.

**Concepts you'll learn:** energy gradients as the root of all climate,
vector fields, gradient computation on an irregular mesh, and
advection (the simplest fluid idea there is).

New fields: `temperature`, `precipitation`, `wind_u`, `wind_v`,
`wind_magnitude`, plus mesh-side intermediate `moisture`. New configs:
`InsolationConfig`, `WindConfig`, `MoistureConfig`.

---

## Before you start (house style — read `CONVENTIONS.md`)

> **All code in this phase must match `docs/worldgen-guide/CONVENTIONS.md`.**
> Two layers always: pure functions in a new `src/worldgen/climate/` package,
> thin `Stage` wrappers in `src/worldgen/stages/`. Full type annotations,
> keyword-arg calls, `msg:`-before-`raise`, the §6 prerequisite pattern.

**Files you will create:**

```
src/worldgen/climate/
    insolation.py      # pure: insolation_field(...)
    temperature.py     # pure: compute_temperature(...)
    wind.py            # pure: wind_belts(...), elevation_gradient(...), deflect_wind(...)
    moisture.py        # pure: build_downwind(...), transport_moisture(...)
src/worldgen/stages/
    insolation.py      # InsolationStage
    temperature.py     # TemperatureStage
    wind.py            # WindStage
    moisture.py        # MoistureStage
```

**Fields to add** — one line each in **both** `MeshFields` and `GridFields`
(`src/worldgen/fields.py`), with `dtype` metadata and a `#` comment:

```python
temperature: Float64Array | None = field(default=None, metadata={"dtype": np.float64})     # [0,1] warmth; 1 = sunband
precipitation: Float64Array | None = field(default=None, metadata={"dtype": np.float64})    # [0,1] rainfall
wind_u: Float64Array | None = field(default=None, metadata={"dtype": np.float64})           # unit wind direction x
wind_v: Float64Array | None = field(default=None, metadata={"dtype": np.float64})           # unit wind direction y
wind_magnitude: Float64Array | None = field(default=None, metadata={"dtype": np.float64})   # [0,1] wind speed
```

`insolation`, `moisture`, `grad_x`, `grad_y`, `downwind` are **mesh-side
intermediates** the viewer may want but the product does not — keep them as
extra `MeshFields` columns (they simply will not be read by gameplay) **or** as
locals threaded through the stages; match how Phase 1 kept `z_route`/`receiver`
on `ctx.fields`. Recommended: add `insolation` and `moisture` to `MeshFields`
only (not `GridFields`) so they do not widen the product grid.

**Configs to add** (`config/worldgen_config.py`, then register on
`WorldgenConfig` with `default_factory` — see `CONVENTIONS.md` §8):
`InsolationConfig`, `WindConfig`, `MoistureConfig`. Suggested fields are listed
in each step's scaffold below.

**Noise constants** — append to `src/worldgen/noise/rng.py`:

```python
FIELD_INSOLATION_WOBBLE: int = 4
FIELD_WIND_U: int = 5
FIELD_WIND_V: int = 6
```

**Pipeline** — append in order to `_build_stages()` (`pipeline.py`):
`InsolationStage(), TemperatureStage(), WindStage(), MoistureStage()`.

---

## Step 1 — The insolation field (1 h)

### The lesson first

Recall the planning decision: this world is a torus, so latitude doesn't
exist — instead we *author* the energy pattern. One ring around the world runs
hot (call it the sunband), the opposite ring cold (the frostbelt). Everything
else in this phase derives from that one declaration, which is why it gets its
own config and stage instead of being a buried cosine.

### What to build

`InsolationStage`, writing a mesh intermediate `insolation` in [0, 1]:

```python
phase      = 2 * np.pi * sites_y / height * cfg.bands     # bands = 1
insolation = (np.cos(phase) + 1.0) / 2.0                  # hot ring at y = 0
insolation = 0.5 + (insolation - 0.5) * cfg.contrast      # contrast knob
```

Optionally warp `sites_y` with low-frequency noise first (`cfg.wobble`) so the
rings aren't laser-straight — port the warp idea from the old climate code.

**Check (viewer):** an `insolation` layer: a smooth hot band, a smooth cold
band, wrapping seamlessly. Two minutes of work after Phase 1; enjoy it.

### Implementation scaffold (house style)

`climate/insolation.py`:

```python
def insolation_field(
    *,
    geometry: MeshGeometry,
    cfg: InsolationConfig,
    wobble_noise: FractalField | None = None,
) -> Float64Array:
    """Authored energy field in [0, 1]: hot ring at y = 0, cold ring opposite."""
```

`InsolationConfig`:

```python
@dataclass
class InsolationConfig:
    """Authored energy pattern (no latitude on a torus)."""

    bands: int = 1          # Number of hot/cold ring pairs around the torus
    contrast: float = 1.0   # Spread of climate zones; <1 flattens, >1 sharpens
    wobble: float = 0.0     # Low-freq noise warp on the ring lines; 0 = laser-straight
```

`InsolationStage.run`: build `wobble_noise` (only if `cfg.wobble > 0`) via
`FractalField(sampler=ctx.noise_for("insolation_wobble"), field_id=FIELD_INSOLATION_WOBBLE, octaves=3)`,
call `insolation_field(...)`, assign `ctx.fields.insolation`.

**Definition of done:** field in `[0, 1]`; `insolation[y=0] ≈ 1`; wraps (the
value at `y=0` equals `y=height`). Viewer layer added.

**Pitfalls:** use `geometry.sites[:, 1]` for `y` and divide by
`geometry.height` (not `size`); the `cos` term must use `2π·y/height·bands` so it
wraps — a raw `y` term will seam.

---

## Step 2 — Temperature (1–2 h)

Three physical effects, three array expressions, in order:

1. **Base**: `temperature = insolation`.
2. **Lapse rate** (mountains are cold): subtract
   `cfg.lapse_rate * np.maximum(0.0, elevation)`. Note `elevation` is the
   contract form — land in (0, 1] — so the scale is world-relative, which is
   what we want.
3. **Maritime moderation** (coasts are mild): ocean buffers temperature, and
   the buffering decays inland. Compute a maritime weight
   `w = exp(-coast_distance / cfg.maritime_reach)` (1 at the coast, →0 deep
   inland; ocean cells get `w = 1`), then pull temperature toward the *sea
   temperature at that y* (which is just `insolation` — the ocean surface
   tracks the energy field):
   `temperature += w * cfg.maritime_strength * (insolation - temperature)`.
   Continental interiors keep their extremes; coastlines soften.

Clamp to [0, 1] at the end.

**Check (viewer):** `temperature` layer. You should see: cold frostbelt ring,
hot sunband, *visible cool spots on every mountain range* (lapse), and gentler
gradients along coasts than deep inland (maritime). All four causes legible in
one image — if one is missing, its term is wrong.

### Implementation scaffold (house style)

`climate/temperature.py`:

```python
def compute_temperature(
    *,
    insolation: Float64Array,
    elevation: Float64Array,
    coast_distance: Float64Array,
    is_land: BoolArray,
    cfg: TemperatureConfig,
) -> Float64Array:
    """Insolation, modified by lapse rate (cold peaks) and maritime moderation."""
```

`TemperatureConfig`:

```python
@dataclass
class TemperatureConfig:
    """Lapse rate and maritime moderation on top of insolation."""

    lapse_rate: float = 0.5         # Cooling per unit land elevation
    maritime_reach: float = 4.0     # Coast-distance decay length for ocean moderation
    maritime_strength: float = 0.4  # How strongly coasts pull toward sea temperature
```

`TemperatureStage.run`: narrow the four input fields with the §6 prerequisite
pattern (`insolation`, `elevation`, `coast_distance`, `is_land` must all be set),
call `compute_temperature(...)`, assign `ctx.fields.temperature`.

**Definition of done:** pure array math, **zero loops**; result clamped to
`[0, 1]` with `np.clip`; ocean cells use `w = 1` (full moderation). Viewer layer
added.

**Pitfalls:** `np.maximum(0.0, elevation)` (not `abs`) so ocean depths do not
"cool"; build the maritime weight as `np.where(is_land, np.exp(-coast_distance /
reach), 1.0)`; apply the three effects in the stated order.

---

## Step 3 — Wind belts (2 h)

### The lesson first

Air rises over the hot ring, sinks over the cold ring, and the space between
organizes into belts of prevailing wind — that's the real Hadley circulation,
and we author its *time-averaged result* rather than simulate it (planning
decision: circulation sims are weather's job, and weather is a future system).

A belt pattern that wraps correctly is just sinusoids of the ring phase. Port
the *shape* of the old `_generate_wind` (it was reasonable), re-derived from
ring phase instead of fake latitude:

```python
base_u = -np.cos(phase * cfg.belt_count)        # zonal (east-west) belts
base_v =  np.sin(phase * cfg.belt_count) * cfg.meridional_strength
```

Add FBm turbulence per component (two `NoiseSource`s, named
`"wind_u"`/`"wind_v"` — sub-seeding means they're independent), then
normalize: store unit direction in `wind_u/wind_v` and length in
`wind_magnitude`.

**Check (viewer):** a wind layer. Easiest readable encoding in a terminal:
color by direction angle (hue = `atan2(v, u)`), brightness by magnitude. You
want coherent belts with turbulent wobble, not static.

### Implementation scaffold (house style)

`climate/wind.py` (steps 3 **and** 4 live here):

```python
def wind_belts(
    *,
    geometry: MeshGeometry,
    cfg: WindConfig,
    turbulence_u: FractalField,
    turbulence_v: FractalField,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Return (wind_u, wind_v, wind_magnitude): zonal belts + FBm turbulence, normalized."""
```

`WindConfig` (add deflection knobs now; step 4 uses them):

```python
@dataclass
class WindConfig:
    """Prevailing wind belts and terrain deflection."""

    belt_count: int = 3                # Zonal belts around the ring
    meridional_strength: float = 0.3   # North-south component amplitude
    turbulence: float = 0.4            # FBm wobble amplitude on each component
    deflection: float = 0.5            # How hard wind bends away from uphill (step 4)
```

`WindStage.run`: build two independent `FractalField`s from
`ctx.noise_for("wind_u")` / `ctx.noise_for("wind_v")` with `FIELD_WIND_U` /
`FIELD_WIND_V`, call `wind_belts(...)`, then `elevation_gradient(...)` +
`deflect_wind(...)` from step 4, then assign `wind_u/wind_v/wind_magnitude`.

**Definition of done:** where `wind_magnitude > 0`, `(wind_u, wind_v)` is
unit-length; belts wrap; two noise sources are independently sub-seeded.

**Pitfalls:** normalize **after** adding turbulence; guard divide-by-zero
(`mag = hypot(u, v); u = u/mag where mag>0 else 0`); the two turbulence fields
must use different `noise_for` names or they will be identical.

---

## Step 4 — Terrain deflection (1–2 h)

### The lesson first

Wind doesn't blow *through* a mountain range; it deflects around and channels
through passes. Full fluid dynamics is overkill; the cheap trick that looks
right: push the wind vector away from "uphill."

You need the **elevation gradient** on an irregular mesh: for cell `i`,

```python
grad = Σ_j  (z[j] - z[i]) / |d_ij|²  ·  d_ij      summed over neighbors j
```

where `d_ij` is the torus-aware site offset (your `torus_delta` again). This
weighted sum points uphill. (Compute it once here, store as mesh intermediates
`grad_x/grad_y` — Phase 1's `slope` was just its magnitude cousin.)

Deflection: subtract the uphill component from the wind, scaled by how hard
the wind runs into the slope:

```python
into_slope = max(0, wind · grad_unit)             # only when blowing uphill
wind      -= cfg.deflection * into_slope * grad_unit
```

then re-normalize direction/magnitude. Result: flow bends to run *along*
ranges and accelerates through gaps — exactly the visual signature to look for.

**Check (viewer):** wind layer again, eyes on a big mountain range: arrows/hue
should shear sideways along the windward flank.

### Implementation scaffold (house style)

Two pure functions in `climate/wind.py`:

```python
def elevation_gradient(
    *,
    geometry: MeshGeometry,
    elevation: Float64Array,
) -> tuple[Float64Array, Float64Array]:
    """Per-cell uphill gradient (grad_x, grad_y) via distance-weighted neighbor sum on the torus."""


def deflect_wind(
    *,
    wind_u: Float64Array,
    wind_v: Float64Array,
    grad_x: Float64Array,
    grad_y: Float64Array,
    cfg: WindConfig,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Subtract the uphill-into-slope component from wind; return renormalized (u, v, magnitude)."""
```

**Definition of done:** gradient uses `torus_delta` for every `d_ij` (per
`CONVENTIONS.md` §11); `into_slope = max(0, wind·grad_unit)` (only when blowing
uphill); wind renormalized after deflection. Store `grad_x/grad_y` as mesh
intermediates — moisture step reuses neighbor offsets, not these, but they are
cheap to keep.

**Pitfalls:** the weighted sum `Σ (z[j]-z[i])/|d|² · d` points **uphill**;
subtract it (do not add). Skip `|d| == 0`. Guard the renormalize divide-by-zero
exactly as in step 3.

---

## Step 5 — Moisture transport (3–4 h)

### The lesson first

This is the one true (small) simulation of the phase, and the payoff of the
whole climate design. The idea — **advection** — is just "stuff is carried by
flow": moisture evaporates from the ocean, rides the wind, and falls out as
rain, preferentially when forced uphill or chilled.

Discrete version on the mesh, per pass, per cell: moisture moves from cell `i`
to its **downwind neighbor** — the neighbor `j` whose direction
`torus_delta(site_i → site_j)` best aligns with `wind_i` (max dot product;
precompute this `downwind[]` array once after step 4, it doesn't change).

The loop (~`cfg.passes` ≈ 30):

```
moisture[ocean] = evaporation = cfg.evap * temperature[ocean]   # refill source
for each cell i (any order, double-buffered):
    j        = downwind[i]
    uphill   = max(0, z[j] - z[i])                  # orographic forcing
    chill    = max(0, temperature[i] - temperature[j])
    rainout  = clip(cfg.base_rain + cfg.oro * uphill + cfg.chill * chill, 0, 1)
    rain     = moisture[i] * rainout
    precipitation[i] += rain
    new_moisture[j]  += moisture[i] - rain          # remainder travels on
```

**Double-buffered** means: read from `moisture`, accumulate into a fresh
`new_moisture`, swap at the end of the pass — same reason as diffusion in
Phase 1 (in-place updates make results depend on iteration order).

After the loop, normalize `precipitation` to [0, 1] (e.g., divide by its 99th
percentile and clip — a single freak cell shouldn't compress the whole scale).

### Why the classics emerge

Trace the algorithm in your head and you can predict the map before running
it: ocean → coast = moist air arrives loaded → wet coast. Each inland step
loses `base_rain` → exponential drying inland. Mountain in the way → `uphill`
dumps the load on the windward side → nothing left behind → **rain shadow**.
Cold frostbelt ocean → low evaporation → dry. That's four climate clichés from
eight lines.

**Check (viewer):** `precipitation` layer next to the wind layer. Verify each
prediction above *by looking*. The rain shadow behind your biggest range is
the acceptance test of the entire phase.

### Implementation scaffold (house style)

`climate/moisture.py`:

```python
def build_downwind(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
) -> Int32Array:
    """For each cell, the neighbor whose direction best aligns with the wind (max dot product)."""


def transport_moisture(
    *,
    geometry: MeshGeometry,
    downwind: Int32Array,
    temperature: Float64Array,
    elevation: Float64Array,
    is_land: BoolArray,
    cfg: MoistureConfig,
) -> Float64Array:
    """Advect ocean-sourced moisture downwind, raining it out; return precipitation in [0, 1]."""
```

`MoistureConfig`:

```python
@dataclass
class MoistureConfig:
    """Ocean-sourced moisture advected downwind and rained out."""

    passes: int = 30           # Advection iterations
    evaporation: float = 1.0   # Ocean moisture refill scale (× temperature)
    base_rain: float = 0.05    # Fraction rained out per inland step (drying rate)
    oro: float = 0.6           # Orographic (uphill) rainout multiplier
    chill: float = 0.3         # Temperature-drop rainout multiplier
```

**Definition of done:** the per-pass loop is **double-buffered** (read
`moisture`, accumulate into fresh `new_moisture`, swap) — see `CONVENTIONS.md`
§9; `downwind` is precomputed once; final `precipitation` normalized by its 99th
percentile then `np.clip(…, 0, 1)`.

**Pitfalls:** refill `moisture[ocean] = evap * temperature[ocean]` at the **start
of every pass**, not once; `rainout` clipped to `[0, 1]`; the
`moisture[i] - rain` remainder goes to `new_moisture[downwind[i]]`, never back to
`i`. A non-buffered in-place loop is a determinism bug **and** a directional-bias
bug.

---

## Step 6 — Tuning and tests (1–2 h)

Pipeline order now:
`Mesh → Plates → BoundaryUplift → Erosion → Finalize → Insolation →
Temperature → Wind → Moisture`.

Tune: `contrast` (climate-zone spread), `maritime_reach/strength`,
`base_rain` (inland drying distance — too high and only coasts are wet, too
low and moisture crosses the continent unspent), `oro` (rain-shadow drama),
`evap` (overall wetness).

Tests to add:

- Ranges: `temperature`/`precipitation` in [0, 1]; wind direction unit-length
  where magnitude > 0.
- Causality smoke test: mean precipitation of land cells with
  `coast_distance ≤ 2` exceeds mean of cells with `coast_distance ≥ 10`
  (coasts wetter than interiors — coarse, seed-parameterized, catches sign
  bugs in the transport loop).
- Determinism (always).

### Test scaffold (house style)

New `test/worldgen/test_climate.py` (Phase 5 will fold this into
`test_climate_ecology.py`). Use the fast fixture (`cell_count=500`, `size=40`),
parameterize over 2–3 seeds, one-line docstring per test:

```python
@pytest.mark.parametrize("seed", [1, 7, 42])
def test_temperature_and_precip_in_unit_range(seed: int) -> None:
    """Climate fields stay in [0, 1]."""
    ctx = WorldgenPipeline(FAST_CONFIG).run(seed=seed, size=FAST_SIZE)
    assert float(ctx.fields.temperature.min()) >= 0.0
    assert float(ctx.fields.temperature.max()) <= 1.0
    # precipitation likewise


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_coasts_wetter_than_interiors(seed: int) -> None:
    """Transport loop carries ocean moisture inland and spends it (sign check)."""
    # mean precip of land cells with coast_distance <= 2  >  mean with >= 10
```

**Definition of done:** range test, causality smoke test, and a determinism
assertion all green across every parameterized seed.

## Exit criteria

- [ ] Insolation/temperature/wind/precipitation layers in the viewer
- [ ] Visible: cold mountains, mild coasts, wind belts deflecting around
      ranges, wet windward coasts, dry interiors, at least one honest rain
      shadow
- [ ] Range + causality + determinism tests green

**Phase 3** sends this rain down the mountains: discharge, rivers with names
waiting to happen, and lakes that finally spill.
