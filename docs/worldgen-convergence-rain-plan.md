# Worldgen Convergence Rain Plan

Status: **implemented.** See "Implementation notes & divergences" at the bottom
for what shipped and where it differed. A guide for replacing the authored
Gaussian rain belts with rain derived from **wind convergence**, so the
latitudinal wet/dry banding becomes a *consequence* of the prevailing wind field
rather than a second, independently-tuned authoring of the same latitude
structure. Scope: `src/worldgen` climate phase (`climate/wind.py`,
`climate/moisture.py`) plus its config/validation surface.

This is the future-work item logged in `worldgen-ocean-currents-plan.md` §6 and
the convergence-rain note in `worldgen-sanity-plan.md`. It is a **climate
refinement, not a weather feature** (see §2) and is intended to land **before**
the weather/seasonality layer, because it is the mechanism that later makes
seasonal ITCZ migration emerge for free.

---

## 0. The standard (inherited)

Same as the sanity plan and ocean-currents plan: **causal plausibility in
service of legibility**, on a torus that is **one whole planet**, emitting
**climatic normals** (not weather), with **no Coriolis** (belt directions are
authored from latitude) and **no shape-knob fudges** where a physical mechanism
will do.

---

## 1. Decisions (interview log)

| # | Decision |
|---|----------|
| 1 | **Categorization: this is climate, not weather.** Convergence of the *prevailing* (mean) wind is itself a climatic normal; it produces the mean rain pattern, which is climate's job. The weather layer handles temporal variation and would not naturally contain it (§2). |
| 2 | **Motivation is coherence + first-principles.** Today the three-cell wind belts and the Gaussian ITCZ/temperate precip belts are *two parallel authorings of the same latitude structure*, independently tuned and free to drift. Deriving rain from wind convergence collapses them to **one source of truth** (the wind field). |
| 3 | **Strategy A — convergence as a rainout term.** Add a discrete **divergence operator** on the wind field; feed **convergence** (`max(0, −∇·wind)`) into the moisture rainout alongside the existing orographic and chill terms. The latitudinal banding then emerges cell-by-cell from where wind converges, not from an authored latitude curve. (Rejected: strategy B, computing a convergence *profile in latitude* and using it as the belt multiplier — keeps the parallel-authoring shape we are trying to remove.) |
| 4 | **Authored belt knobs become trim, not primary.** Keep `precip_belt` available but down-weighted, so the known-good tuning is a dial we can lean on if the emergent bands wobble — not the primary driver. Target end state: belts contribute little or nothing and convergence carries the banding. |
| 5 | **Order before weather.** Land this as its own climate PR ahead of the weather layer: seasonal rain migration should fall out of seasonally-shifted wind belts → shifted convergence → shifted rain, with no separate authoring of belt migration. |
| 6 | **Behavior-changing, not a refactor.** Unlike the diffuse/transport unifications, this *changes the rain pattern* and reopens the moisture tuning. It ships only when the biome plausibility bands and census stay healthy (§6). |

---

## 2. Why this is climate, not weather

`∇·wind < 0 → rising air → rain` is computed from the **prevailing** wind — the
authored three-cell belts, which are a **climatic normal**. The divergence of a
time-averaged field is itself a time-average, so convergence-driven rain is a
*mean* rain pattern, exactly what the precip baseline already represents. The
ITCZ as "where the trade winds converge" is a climatological feature, not a
storm.

The weather layer, by contrast, is about **temporal** variation (seasons,
storms, day↔night). It does not own the mean rain pattern. Deferring this "to
weather" would leave the mean pattern homeless. The genuine weather hook is the
*opposite* direction: once rain is convergence-derived, the weather layer's
seasonal wind shift makes the rain belts migrate **for free** — which is the
§5 reason to do this first.

---

## 3. The model

### 3.1 Divergence operator (`climate/wind.py`)

Add a scalar **wind divergence** per cell, the divergence-flavoured analogue of
the existing `elevation_gradient` (which already does a torus-aware,
distance-weighted neighbour sum). For cell `i` with wind vector
`w_i = (wind_u, wind_v)` and torus offset `d_ij` to neighbour `j`:

```
div_i = Σ_{j∈N(i)}  (w_j − w_i) · d_ij  /  |d_ij|²
```

* `d_ij` is the minimum-image offset from `torus_delta` (seam-safe, deterministic).
* `(w_j − w_i) · d_ij > 0` means wind speeds up in the outward direction →
  **divergence**; `< 0` means it slows/reverses toward `i` → **convergence**.
* **Convergence** is `convergence_i = max(0, −div_i)`, normalized to `[0, 1]`
  (divide by a high percentile of land+ocean convergence so the scale is stable
  across seeds, mirroring how the codebase normalizes slope/rainout).

This reuses the wind field that already exists post-`WindStage` (belts +
meridional component + turbulence + terrain deflection), so convergence picks up
**three** sources at once: the Hadley/Ferrel/Polar band structure (the ITCZ and
subpolar lows), turbulence-driven local convergence, and terrain-channelled
convergence at ranges/passes. The first reproduces the authored bands; the
others add legible local structure the Gaussian belt never could.

**Sanity of the band structure:** the zonal component `u` is ~latitude-only
(`∂u/∂x ≈ 0`), so `div` is dominated by `∂v/∂y` — the meridional gradient. With
`v = meridional_strength · sin(3π|lat|) · hemi`, convergence falls at the
equator (Hadley inflow) and ~60° (subpolar), divergence at ~30° (subtropics) and
the poles: **wet equator, dry subtropics, wet temperate, dry poles** — the exact
banding currently authored as Gaussians, now emergent.

### 3.2 Convergence rainout (`climate/moisture.py`)

`transport_moisture` already builds a fixed per-cell `rainout` from base drying,
orographic uplift, and temperature chill. Add convergence as a fourth,
physically-parallel uplift term:

```
rainout = clip(base_rain + oro·uphill + chill·chill + conv·convergence, 0, 1)
```

Converging air rises and rains; the moisture must still be *present* (advected in
from the ocean), so dry-air convergence over a deep interior correctly produces
little rain, while the moist equatorial/temperate convergence zones rain hard.
This is more correct than the multiplicative Gaussian belt, which rained the
ITCZ even where no moisture had arrived.

### 3.3 Belt transition (`climate/moisture.py::precip_belt`)

The authored belt becomes **trim**, not the primary driver:

* Phase in: keep `precip_belt` as the post-advection multiplier but reduce its
  authority (e.g. blend `belt` toward 1.0 by a `belt_trim` weight), and let the
  convergence rainout carry the banding.
* Target: `belt_trim → 1` (belt removed) once convergence reproduces the bands
  within the plausibility envelope. The `belt_*` knobs remain in config as the
  documented fallback (§1.4).

---

## 4. Code changes

| File | Change | Rewrite vs edit |
|---|---|---|
| `climate/wind.py` | **New** `wind_divergence(...)` (scalar per cell) + `convergence(...)` normalizer, mirroring `elevation_gradient`. | New functions |
| `stages/wind.py` | Compute convergence after deflection; write a new `convergence` field. | Edit |
| `fields.py` | Add `convergence` to `MeshFields` **and** `GridFields`. | Edit |
| `climate/moisture.py` | Add the `conv·convergence` rainout term; reduce `precip_belt` authority via `belt_trim`. | Edit |
| `stages/moisture.py` | Thread `convergence` into `transport_moisture`. | Edit |
| `config/worldgen_config.py` | Add `convergence_weight`, `convergence_percentile`, `belt_trim` to `MoistureConfig` (and any divergence knob to `WindConfig`). | Edit |
| `scripts/worldgen_render.py` | Add a **Convergence** layer (diverging palette: convergence wet/blue, divergence dry/tan) to the Climate group. | Edit |
| `bake/grid.py` | Picks up `convergence` automatically via the generic path. | None |

### Proposed config (starting defaults — eyeball-tune)

```python
# MoistureConfig additions
convergence_weight: float = 0.6        # rainout per unit normalized convergence
convergence_percentile: float = 90.0   # convergence percentile mapped to 1.0
belt_trim: float = 0.5                 # 0 = full authored belt, 1 = belt removed
```

`convergence` is a physical quantity (a normalized rate), `convergence_weight`
is a rainout coefficient like `oro`/`chill`, and `belt_trim` is the transition
dial — no shape fudges, consistent with the project standard.

---

## 5. Validation

Extends `test/worldgen/test_plausibility.py` and a new
`test/worldgen/test_convergence.py`.

### Hard invariants
| Invariant | Assertion |
|---|---|
| Range | `convergence ∈ [0, 1]`; `precipitation ∈ [0, 1]`. |
| Seam continuity | `convergence` continuous across both torus seams (existing harness). |
| Determinism | identical `convergence`/`precipitation` for identical seed. |

### Signature bands (prove it does the thing)
| Signature | Assertion (conservative — tune) |
|---|---|
| **ITCZ emerges** | mean precipitation in the equatorial band exceeds the subtropical band (wet equator, dry ~30°) **without** the authored Gaussian (`belt_trim = 1`). |
| **Convergence ↔ rain** | high-convergence cells are wetter on average than high-divergence cells, controlling for moisture availability. |
| **Bands survive de-authoring** | with `belt_trim = 1`, the biome plausibility bands still hold (`≥6 biomes, none >45%, cold land <55%`). |

### Regression guard (the real risk)
This **changes worlds**. Re-run `scripts/census.py` across presets/seeds and
confirm the biome mix and HYPER_ARID share stay in the sane envelope the sanity
plan established. Treat a failure here as "re-tune `convergence_weight` /
`belt_trim`", not "ship it".

---

## 6. Phasing

| Phase | Deliverable |
|---|---|
| A | **Divergence field.** `wind_divergence` + `convergence` normalizer; `convergence` field + Convergence viewer layer. Visible, not yet consumed. |
| B | **Convergence rainout.** Add the `conv·convergence` term to `transport_moisture` with the authored belt still primary (`belt_trim = 0`). Confirm rain intensifies in convergence zones. |
| C | **De-author the belt.** Raise `belt_trim` toward 1, re-tune `convergence_weight`, and validate the ITCZ/subtropics banding emerges from convergence alone. Lock the plausibility bands + census. |
| D | **Docs.** Update `worldgen-sanity-plan.md` and `worldgen-ocean-currents-plan.md` §6 to "implemented"; note the seasonal-migration hook for the weather layer. |

---

## 7. Future work / weather hook

Once rain is convergence-derived, the **weather/seasonality layer** gets ITCZ
migration for free: shift the wind belts' latitude phase seasonally → the
convergence zone shifts → the rain belt migrates (monsoon onset/retreat) with no
separate authoring. That is the payoff of doing this in climate first, and the
reason this plan is sequenced ahead of weather.

The SST→wind coupling (deferred in the ocean-currents plan as a cycle/weather
concern) also composes here: if the weather layer ever lets warm SST nudge the
wind, the convergence — and therefore the rain — follows automatically.

---

## 8. Implementation notes & divergences

What shipped, and where it diverged from the map above:

- **The field became signed** (`convergence ∈ [-1, 1]`, a *vertical-motion*
  field: + rising/converging, − sinking/diverging) rather than the planned
  convergence-only `[0, 1]`. This was the key divergence and it was necessary:
  strategy A's rising-only term could only *add* rain at the ITCZ, never
  *suppress* it in the subtropics, so with the belt off the subtropics stayed
  wet (even inverted on pangaea). Signing it lets one field carry the whole
  banding — wet ITCZ/subpolar **and** dry subtropics — and made `belt_trim = 1`
  (belt fully retired) viable, the plan's target end state.
- **Convergence smoothing was added** (not in the original plan): the raw
  neighbour-difference divergence is turbulence-noisy, and a climatic normal must
  be smooth (decision-4 territory). Three `diffuse` passes (reusing the unified
  field-ops primitive) drop the turbulence-scale noise and keep the
  belt/terrain-scale signal. Without it the coarse-mesh `coasts > interiors`
  invariant flickered; with it, that invariant holds at coarse and production
  resolution.
- **`belt_trim` ships at 1.0** (authored belt off by default); convergence
  carries the banding. The `belt_*` and `belt_trim` knobs remain as the
  documented fallback (decision 4). The belt-off biome mix is actually *healthier*
  — forest/woodland/wetland-leaning rather than the belt-on `ice_sheet`/
  `cold_desert` extremes.
- **No new stage / no pipeline reorder**: convergence is computed inside
  `WindStage` (it needs only the finished wind field), so the climate order is
  unchanged. New config lives in `WindConfig` (`convergence_percentile`,
  `convergence_smoothing_*`) and `MoistureConfig` (`convergence_weight`,
  `belt_trim`).
- **Validation:** `test_convergence.py` (divergence of uniform wind = 0; signed
  bounded field; ITCZ convergence > subtropics; equator wetter than subtropics
  with the belt off; determinism). Full worldgen suite green (243 tests);
  plausibility biome bands and the within-band `coasts > interiors` invariant
  hold.
