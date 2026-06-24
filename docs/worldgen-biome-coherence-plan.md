# Worldgen Biome Coherence — Design Plan

*Status: design (not yet implemented). Author-facing guide; implement on
`claude/serene-fermi-2b2kts`.*

## Problem

The dominant-biome map looks **splotchy**: within a clean temperature band the
biome whiplashes between arid and humid types across a handful of tiles,
producing confetti instead of coherent ecoregions.

Empirical triage (seed 7, viewer export of every layer) shows the rest of the
pipeline is **healthy** — plates, uplift/volcanism belts, drainage/rivers/lakes,
temperature/SST/insolation, and the leyline web all look sane. The splotch is
**not** generated in the biome stage; it is **inherited** from upstream, through
this chain:

```
wind turbulence  →  convergence (still marbled after 3 smoothing passes)
                 →  precipitation rainout + advection along turbulent wind
                 →  marbled precipitation  →  splotchy biomes
```

Three stacked contributors, in order of impact:

1. **Precipitation is near-binary / marbled.** Temperature is a clean
   latitudinal gradient; precipitation is a high-contrast, camo-textured field.
   Since `biome = f(temperature, precipitation)`, precipitation noise shreds
   biomes. **Confirmed: the marbling appears on flat land too, so it is wind-
   turbulence noise, not meaningful orographic detail.** Precipitation is the
   one climate field that never gets a spatial smoothing pass — its only
   "smoothing" is the saturating contrast curve, which remaps per-cell values
   but does nothing spatially.
2. **The biome-weight diffusion fights a symptom.** `smooth_biome_weights`
   (4 passes) rounds region edges into blobs but cannot undo strong upstream
   precip contrast.
3. **The render palette amplifies the perception.** `hue = (col * φ) % 1` spaces
   biome hues by golden ratio over *column index*, so climatically-adjacent
   biomes get maximally-different colors — real ecotones render as collisions.

## Target

**Coherent ecoregions with smooth ecotones** (Earth-like): broad
temperature-driven bands, internally graded into smooth wet→dry biome sweeps,
where neighboring biomes are always *climatic* neighbors. Variety is preserved
— a traveler still crosses many biomes pole-to-equator and coast-to-interior —
it just arrives as legible bands instead of static.

This is what `smooth_biome_weights` already *aims* for; we fix the cause one
layer upstream rather than keep sanding the symptom.

## Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Target look | Coherent ecoregions, smooth ecotones |
| 2 | Primary lever | Make **precipitation** coherent upstream; **do not touch** the wind belts / wind-flux work |
| 3 | Smoothing degree | **Climatic-normal** sweet spot — remove the turbulence-noise layer, keep latitude belts + broad rain shadows. *Not* max smoothing (which would flatten into a bland gradient and collapse variety) |
| 4 | Mechanism | **Two-stage (Option 2) up front:** (a) a land-masked `diffuse()` pass on the **precipitation output**, AND (b) raise the existing **convergence** smoothing passes |
| 5 | Biome-weight diffusion | **Keep it** (it makes ecotones gradual — target's second half), but **retune lighter** after seeing results; it no longer has to fight marbling |
| 6 | Render palette | Replace golden-ratio hue with a **2-D climate colormap** (temperature × precipitation). **Viewer/export only — does not ship; does not affect gameplay** |
| 7 | Acceptance | **Dual-guard** metrics (coherence *and* variety) + multi-seed visual |
| 8 | Scope | The precip→biome coherence fix + two secondary cosmetic/quality items below |
| 9 | Elevation relief | **Cosmetic colormap fix only** — relief is real (land p99 = 0.90, peaks at 1.0); the viewer just hides it. No erosion/terrain change |
| 10 | Savagery | Add a `diffuse()` pass; **start at 2 passes**, escalate toward 4 only if band-confetti remains. Also self-heals partly from the precip fix |

### Why two-stage (Decision 4)

Precipitation picks up marbling through **two doors**:

- **Convergence rainout term** — `rainout += convergence_weight * convergence`,
  and convergence is under-smoothed.
- **Advection** — moisture fans *along turbulent wind directions*, so wet
  streaks / dry shadows form on wind streamlines even if convergence were
  perfectly smooth.

Raising convergence passes closes the first door early (before the noise is
baked into sharp wet/dry contrast). The precip output smooth closes **both**
(it is the catch-all, and the only field biomes read). Doing both lets each
stage stay *gentle*, so real coastal/orographic features survive — versus a
single hard end-smooth that softens real gradients along with noise.

The wind field itself is **left untouched**: its turbulence also feeds ocean
currents and coastal temperature moderation, and the recent wind-flux /
convergence-rain work is good. We intervene strictly *below* the wind.

## Implementation

All smoothing reuses the existing shared primitive
`src/worldgen/geometry/field_ops.py::diffuse(geometry, field, strength, passes,
mask=...)` (Jacobi neighbour-mean; double-buffered; deterministic; masked cells
are held at 0 after each pass, and only masked neighbours contribute to the
mean — so a land mask keeps ocean zeros from bleeding into coasts).

### 1. Precipitation output smoothing — *primary fix*

**File:** `src/worldgen/climate/moisture.py`, end of `transport_moisture(...)`
(it already has `geometry` and `is_land` in scope). Apply as the **final step**,
after the belt × modulation multiply and the `precip_gamma`, so the field that
ships to biomes is the climatic-normal.

**Preserve ocean precipitation.** `precipitation` is a baked grid field that
ships in `WorldData`; ocean values are part of the data contract (even though
the only in-worldgen readers — biomes and savagery harshness — are land-only).
So do **not** use a single `mask=is_land` smooth: `diffuse(mask=is_land)` zeroes
ocean cells and would destroy that data. Smooth **land and ocean as two separate
masked domains**, so each smooths only among its own cells (no wet-ocean bleed
into coastal land, no dry-land bleed into coastal ocean) and ocean precip is
both preserved and tidied:

```python
land_p = diffuse(
    geometry=geometry, field=precipitation,
    strength=cfg.precip_smoothing_strength,
    passes=cfg.precip_smoothing_passes, mask=is_land,
)   # ocean cells are 0 here
sea_p = diffuse(
    geometry=geometry, field=precipitation,
    strength=cfg.precip_smoothing_strength,
    passes=cfg.precip_smoothing_passes, mask=~is_land,
)   # land cells are 0 here
precipitation = np.where(is_land, land_p, sea_p)
```

(If ocean-precip coherence turns out not to matter, the cheaper variant is to
smooth land only and restore ocean originals:
`precipitation = np.where(is_land, land_p, precipitation)`. Either way, ocean
values must survive.)

**Future ocean biomes are not rain-determined.** Marine biomes will key off
**SST/temperature, depth, and currents** (reef / open ocean / kelp / polar pack
ice), not precipitation — so this land-precip smoothing has no bearing on them.

**Config:** add to `MoistureConfig` in
`src/worldgen/config/worldgen_config.py`:

```python
precip_smoothing_passes: int = 3      # climatic-normal; start 3, tune 2–5
precip_smoothing_strength: float = 0.5
```

### 2. Convergence smoothing — *second stage*

**File:** `src/worldgen/config/worldgen_config.py`, `WindConfig`. Raise the
existing knob (the field already declares itself a "climatic normal"; it is
simply under-smoothed):

```python
convergence_smoothing_passes: int = 3   # → raise, e.g. 6; tune against render
```

No code change in `src/worldgen/stages/wind.py` — it already calls `diffuse`
with these knobs.

### 3. Biome-weight diffusion — *retune lighter*

**File:** `src/worldgen/config/worldgen_config.py`, `BiomeConfig`. After the
precip fix lands and you have rendered output, reduce:

```python
smoothing_passes: int = 4   # → expect ~2; it no longer fights marbling
```

Keep it non-zero: even a perfectly smooth climate gradient produces a hard
`argmax` line where it crosses a band edge, and this pass is what turns that line
into a gradual ecotone. Tune by eye against the dual-guard metrics (below).

### 4. Biome render palette — 2-D climate colormap (viewer only)

**File:** `scripts/worldgen_render.py`. Two call sites color biomes today:

- Per-tile, `colorize_tile` ~L364–370 (`hue = (biome_col * φ) % 1`).
- Vectorized, `colorize` BIOMES branch ~L562–566.

Replace both with a climate-positioned color. Pull the per-column climate
centers from the single source of truth,
`src/worldgen/ecology/biomes.py::derive_centers()` →
`(center_temp, center_precip, biome_order)`, indexed by the biome column
(`argmax` of the weights). Map:

- **temperature center** → cool→warm axis (e.g. blue → red),
- **precipitation center** → dry→wet axis (e.g. desert tan/brown → green/teal).

A simple, legible scheme (Whittaker-style): hue from precipitation
(dry≈40°/yellow → wet≈170°/teal), value/saturation from temperature, or a direct
bilinear blend of four corner colors over `(center_temp, center_precip) ∈
[0,1]²`. Ocean/lake stay `WATER_COLOR`. Result: climatically-adjacent biomes are
perceptually adjacent and the map reads as a smooth climate field — an honest
view of coherence.

This is diagnostic only; the game renders biomes with its own art.

### 5. Elevation colormap — cosmetic (viewer only)

**File:** `scripts/worldgen_render.py`, ELEVATION branch (vectorized ~L475–479;
per-tile ~L242). Today it normalizes by the full range including ocean
(`z_min = -1`), squeezing all land into the top half of a green→tan ramp and
washing out mountains. Fix: normalize **land** by the land range (`0 .. land
max`) and use a hypsometric tint (green → yellow → brown → white). The relief is
already in the data (land p50 = 0.36, p90 = 0.56, p99 = 0.90, max = 1.0); no
terrain/erosion change.

### 6. Savagery smoothing

**File:** `src/worldgen/stages/savagery.py`. Add a `diffuse()` pass after
`compute_savagery(...)`, mirroring the biome stage. Savagery is "legible
danger," consumed as discrete `SavageryBand`s — so single-tile band flips are
actively bad — but its `noise` term is intentional ("nature isn't a formula"),
so we keep *some* texture:

```python
savagery = diffuse(
    geometry=ctx.geometry,
    field=savagery,
    strength=cfg.savagery_smoothing_strength,
    passes=cfg.savagery_smoothing_passes,
    mask=...,   # match how savagery is consumed (land-only vs all cells); verify
)
```

**Config:** add to `SavageryConfig`:

```python
savagery_smoothing_passes: int = 2      # start light; escalate to ~4 if band-confetti remains
savagery_smoothing_strength: float = 0.5
```

Savagery's `harshness` term reads `precipitation` directly, so it also
**self-heals** from the precip fix — re-render before deciding whether to bump
the passes.

## Acceptance — dual-guard + multi-seed visual

The one real risk is **over-smoothing collapsing biome diversity** (confetti →
"three biomes total"). Guard *both* directions.

**Coherence guards (must improve):**
- **Singleton fraction** of dominant biomes drops vs. baseline. There is already
  a singleton-fraction helper and test in
  `test/worldgen/test_climate_ecology.py` — extend/assert against it.
- **Precipitation local variance** (mean over land of per-cell variance against
  neighbour mean) drops materially.

**Variety guard (must hold):**
- **Distinct-biome count on land** (or biome-distribution **entropy**) stays
  above a floor — confirm the world does not collapse to a few biomes.

**Invariants (must still pass):**
- `argmax(biome_weights) == BIOME_GRID` agreement
  (`test_argmax_biome_matches_grid`).
- Every land biome row sums to 1; ocean/lake rows are 0.
- Land fraction stays within `land_fraction_clamp`.

**Visual:** export `precipitation` and `biomes` (with the new climate colormap)
across ~5 seeds; precipitation should read as belts + broad gradients (no camo),
biomes as coherent regions with gradual ecotones.

Encode the coherence/variety guards as **soft** multi-seed assertions (trend vs.
baseline), not brittle absolute thresholds, to avoid seed-dependent flakiness.

## Tuning order (one-directional search)

Smoothing is one-way (you can always add more, but can't recover erased
texture), so search from light → heavy:

1. Land precip smooth `passes = 3`, convergence `passes = 6`. Render.
2. If still marbled: raise precip passes (4–5) and/or convergence passes.
3. If coasts/rain-shadows look softened: back off precip passes, lean on
   convergence instead.
4. Once precip is coherent: drop `BiomeConfig.smoothing_passes` toward ~2.
5. Savagery: start `passes = 2`, bump only if band-confetti persists.
6. Re-check the dual-guard metrics at every step.

## Out of scope

Healthy stages confirmed by triage — **no changes**: plates, uplift, vulcanism,
erosion/terrain structure, drainage, rivers, lakes, temperature, SST,
insolation, wind belts/flux, leylines, magic channels. The wind field is
explicitly left untouched.

## Touched files (summary)

| File | Change |
|------|--------|
| `src/worldgen/climate/moisture.py` | Final land-masked `diffuse` on precipitation |
| `src/worldgen/config/worldgen_config.py` | `MoistureConfig` precip knobs; raise `WindConfig.convergence_smoothing_passes`; retune `BiomeConfig.smoothing_passes`; `SavageryConfig` knobs |
| `src/worldgen/stages/savagery.py` | `diffuse` pass on savagery |
| `scripts/worldgen_render.py` | Biome 2-D climate colormap; elevation hypsometric/land-normalized colormap (viewer only) |
| `test/worldgen/test_climate_ecology.py` (+ `test_plausibility.py`) | Dual-guard coherence/variety assertions |
