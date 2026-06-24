# Worldgen Precipitation Redesign — Design Plan

*Status: design (not yet implemented). Implement on `claude/serene-fermi-2b2kts`.
House style: `docs/worldgen-guide/CONVENTIONS.md`.*

## Problem

Worlds come out **all forest/wetland** — almost no grasslands, deserts, or
shrublands. The biome-region census made it obvious: at the 128 target, land is
~90% Forest+Wetland across seeds, with **0% desert/grassland** for many.

Root-cause investigation (not the parity change, not the smoothing):

- **Size / torus scale:** zero effect (identical metrics at size 96/128/220).
- **Precip smoothing (recent):** zero effect (meanP 0.56 with it on *and* off).
- **The real cause — precipitation has no geographic structure at all:**
  `corr(coast_distance, precip) = +0.00`, and precip by coast→interior quintile
  is **dead flat**. Interiors are exactly as wet as coasts. There are no rain
  shadows, no continentality, no subtropical deserts.

Two compounding mechanisms produced the flat, wet field:

1. **A precipitation floor.** `belt_trim = 1.0` collapses the latitude belt to
   1.0 everywhere, so `belt_adv_floor = 0.35` (meant only to keep the *equatorial
   ITCZ* raining) applies **globally**; `precip_gamma = 0.6` then lifts that floor
   to **~0.53**. No land can be arid — the dry biome bands are unreachable.
2. **The floor is a band-aid over a deeper failure.** The moisture-advection
   model fans moisture to every downwind neighbour and refills the ocean each
   pass, so it floods the continent to a near-uniform saturation. It was changed
   from thin filaments ("interiors bone dry") to a spreading fan ("wets the
   land") — overcorrecting from too-dry to uniformly-wet — and then floored. The
   advected "marbling" we smoothed earlier was *turbulence noise*; it was the
   **only** spatial structure precipitation had. Underneath, the field is flat.

So the biome variety we see comes almost entirely from **temperature
(latitude)**; precipitation contributes noise, not structure.

## Decision: replace the model, don't tune it

Process-simulation of atmospheric moisture transport (advect, deplete, recycle)
is the fragile class of model we just diagnosed as broken — it floods or starves
on a parameter change. Instead, model precipitation by its **geographic causes**
(the *outcomes* of the physics), which is legible, controllable, robust, and the
standard approach for procedural worldgen. This is the **climate normal** (a
long-term average) — it *should* be smooth and geography-driven; weather/
variability is a separate future layer, not baked here.

## Target

A precipitation field where geography is legible: **wet windward coasts, dry deep
interiors, real extended rain shadows, subtropical deserts, cold-current coastal
deserts**, and the planetary bands (wet ITCZ, dry subtropics, wet temperate, dry
poles). No floor; dryness emerges where geography says it should. Worlds keep
individual wet/dry character.

## Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Architecture | **Geography-driven composition**, not process simulation. Iterative moisture advection is removed |
| 2 | Latitude bands | **Authored Gaussian belt re-enabled** as the planetary primary; **convergence demoted** to a secondary perturbation (its signal kept as detail, not discarded) |
| 3 | Continentality | **Isotropic coast-distance decay** (`exp(-coast_distance / reach)`) — most robust; wind asymmetry is the orographic term's job, not this one |
| 4 | Orographic / rain shadow | **Upwind-barrier lookup**: scan a few cells upwind along the wind, find the tallest barrier crossed → shadow (dry, *extended* downwind); wind blowing uphill into a cell → wet. No iterative transport |
| 5 | Composition | **Multiplicative** — `belt × continentality × orographic`; any single dry factor gates the cell |
| 6 | Normalization | **Absolute calibration** — tune driver amplitudes so a typical world spans the bands, clip to [0,1], optional gentle gamma. **No floor, no relative anchor.** Worlds keep wet/dry character |
| 7 | Ocean source | **SST modulates coastal moisture** — warm currents wet coasts, cold currents starve them (Atacama/Namib). Reuses the existing `sst` field |
| 8 | Texture / noise | **None.** This is the climate normal; texture comes from terrain + coastlines in the drivers, not dither. Weather is a separate future layer |

## The model

```
moisture_supply = sst_source(cell) · exp(-coast_distance / reach)      # continentality × ocean source
orographic      = windward_gain(wind·∇elev) · shadow(upwind barrier)   # extended rain shadows
precip_raw      = belt(latitude) · moisture_supply · orographic · (1 + wₚ·convergence)
precip          = clip(precip_raw ^ gamma, 0, 1)                       # absolute; no floor, no anchor
```

- **`belt(latitude)`** — the existing `precip_belt` (equatorial + temperate
  Gaussian wet bumps; dry subtropics = the gap; dry poles = the falloff),
  **re-enabled** (drop `belt_trim`, or set it so the belt is the primary again).
- **`sst_source(cell)`** — ocean sea-surface temperature propagated inland from
  the nearest coast (warm coast → high supply, cold coast → low). Cold-current
  coasts read dry even at `coast_distance ≈ 0`.
- **`exp(-coast_distance / reach)`** — isotropic continentality; deep interiors
  dry regardless of belt.
- **`orographic`** — `windward_gain`: a bonus where `wind·∇elev > 0` (air forced
  up); `shadow`: scan `lookahead` cells upwind along `(wind_u, wind_v)`, take the
  max elevation gain crossed, and dry the cell in proportion (extended lee
  shadow). Bounded, e.g. `orographic ∈ [shadow_min, windward_max]`.
- **`convergence`** — the existing smoothed convergence field as a mild
  multiplicative perturbation (`wₚ` small); keeps continental ITCZ shifts as
  detail without driving the bands.

## Implementation

### Remove (the advection model and its patches)

`src/worldgen/climate/moisture.py`:
- `build_downwind`, `_downwind_means`, `transport_moisture` (the whole
  source→fan→rainout loop).

`MoistureConfig` knobs that go: `passes`, `evaporation`, `base_rain`, `oro`,
`chill`, `wet_anchor_percentile`, `belt_adv_floor`, `belt_trim`,
`convergence_weight` (replaced by the small perturbation weight). The two-stage
precip-smoothing knobs (`precip_smoothing_passes/strength`) are **likely
unnecessary** — the new field is smooth by construction (no advection
turbulence); keep at most a light pass, or drop. Convergence smoothing in
`WindConfig` stays (still a climatic normal).

### Add (the geography drivers — pure functions, keyword-only, typed)

In `src/worldgen/climate/moisture.py` (or a new `climate/precipitation.py`):
- `coastal_sst_source(*, geometry, sst, is_land, coast_distance) -> Float64Array`
  — propagate ocean SST inland from the nearest coast (a BFS/nearest-coast carry,
  reusing the coast-distance machinery).
- `continentality(*, coast_distance, sst_source, cfg) -> Float64Array`.
- `orographic(*, geometry, elevation, wind_u, wind_v, cfg) -> Float64Array` — the
  windward-gain + upwind-barrier shadow (directed look along the wind over CSR
  adjacency; bounded).
- `compute_precipitation(*, latitude, ..., convergence, cfg) -> Float64Array` —
  composes the model above. Keep `precip_belt` (re-enabled).

`MoistureConfig` new knobs (each defaulted + commented, per §8):
`continentality_reach`, `sst_source_min`, `orographic_lookahead`,
`windward_gain`, `shadow_strength`, `shadow_min`, `windward_max`,
`convergence_perturb_weight`, `precip_gamma` (kept, for shaping).

### Wire-up

- `MoistureStage` reads `latitude`, `coast_distance`, `sst`, `elevation`,
  `wind_u/v`, `convergence` from `ctx.fields` and calls `compute_precipitation`.
  `coast_distance` is available: it is written in **FinalizeStage** (Phase 1) by
  `compute_coast_distance`, well before Moisture (already consumed by Temperature
  and Savagery).
- Pipeline order unchanged (`... → Wind → OceanCurrent → Temperature →
  Moisture`); Moisture now consumes geography instead of running transport.
- Viewer: the `precipitation` layer already reads `grid.precipitation` — no
  change.

## Acceptance

The diagnostic that was `+0.00` is the headline metric.

- **Continentality:** `corr(coast_distance, precip)` is now clearly **negative**
  across seeds; precip by coast→interior quintile decreases monotonically.
- **Band coverage / variety:** landscape-category census shows a real spread —
  deserts and grasslands present, Forest not dominating (>~70%) — without a
  relative anchor forcing it. Reuse the biome-region census from
  `scripts/`/tests.
- **Rain shadow:** leeward of a range is drier than its windward side (a directed
  spot-check or test).
- **Cold-current coasts** read drier than warm-current coasts (sst source works).
- **No floor:** `precip.min()` reaches the arid bands (well below 0.3); the
  hyper-arid band is occupied on hot dry land.
- **Determinism** (whole-pipeline) stays green.

Tests: `test_climate_ecology.py`'s coast-wetter-than-interior should now pass
*strongly* (it was weak/incidental before). Add a continentality-gradient test
and a rain-shadow test. Convergence-rain tests that assume convergence *drives*
the banding need re-scoping to "convergence perturbs."

## Out of scope / future

- **Weather layer** (seasonal + interannual variability) — sits on top of this
  normal; explicitly not baked here.
- **Wind-aware continentality** (upwind-ocean fetch) — a more physical drop-in
  for the isotropic decay if ever wanted; the composition slot is unchanged.
- Ocean/marine precipitation values keep shipping (land-only is what biomes
  read), consistent with the biome-coherence plan.
