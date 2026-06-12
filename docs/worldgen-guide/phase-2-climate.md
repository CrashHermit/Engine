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

## Exit criteria

- [ ] Insolation/temperature/wind/precipitation layers in the viewer
- [ ] Visible: cold mountains, mild coasts, wind belts deflecting around
      ranges, wet windward coasts, dry interiors, at least one honest rain
      shadow
- [ ] Range + causality + determinism tests green

**Phase 3** sends this rain down the mountains: discharge, rivers with names
waiting to happen, and lakes that finally spill.
