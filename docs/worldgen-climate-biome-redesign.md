# Worldgen Climate & Biome Redesign

Status: **design — interview-derived, evidence-backed, not yet implemented.**

Scope: `src/worldgen` climate and ecology only. Terrain and hydrology are
**not** in scope — they were verified sane on current `HEAD` during the
interview (see §2). This round makes the **climate fields a true long-term
average** and the **biome map a coherent, interesting product of it**.

This document is the implementation guide. Work it top to bottom; each phase in
§9 ends runnable and visible in the viewer.

---

## 1. The concern, in one line

> "Make sure the worldgen pipeline produces sane *and* interesting outputs."

"Sane" = the fields mean what they claim (a climate *average* is smooth and
coherent; biomes form real regions). "Interesting" = a single world spans a
rich, legible variety of places.

---

## 2. Corrected baseline (what is and isn't broken on HEAD)

The interview started against stale committed PNGs and reached the wrong
premise. Fresh renders + a census + targeted measurement on current `HEAD`
corrected it:

| Concern | Verdict | Basis |
|---|---|---|
| Ribbon continents | **Fixed** — broad, chunky continents | fresh seed-7 elevation |
| Terrain morphology / hydrology | **Sane**, out of scope | fresh renders, census |
| Temperature field | **Structurally sane** (smooth wrapping rings) | fresh temp render |
| Cold/arid "bias" | **Mostly not a bug** — see §4 | analysis |
| Biome speckle | **The real defect** | flip-rate measurement |

The stale PNGs were deleted and `output/` is now git-ignored so renders can
never again be mistaken for current state.

---

## 3. Root-cause diagnosis (measured, not guessed)

The biome map is a 49-colour patchwork (top biome only 6–8% of land). The cause
was isolated by measurement, discarding three plausible-but-wrong hypotheses:

- **Not the classifier.** Raising the IDW `blend_sharpness` 4 → 8 → 16 → 32
  changes the adjacent-cell biome **flip rate by exactly zero** (0.435). The
  neighbours aren't ambiguous ties — they genuinely land in different biome
  cells.
- **Not the climate inputs being conceptually wrong.** Temperature is very
  smooth (mean neighbour Δ = 0.013; only 0.2% of land edges cross a biome
  band). **Precipitation is noisy** (mean neighbour Δ = 0.073; **35.6%** of land
  edges jump more than half a biome band).
- **Not orographic / chill / wind-jitter.** Turning each off leaves the precip
  noise unchanged (0.0725 → 0.0712 with *all* rainout terms off); correlation of
  precip-noise with terrain roughness is only 0.18. More advection passes make
  it **worse**.

**The precip noise is intrinsic to the moisture advection operator.** It is a
non-conservative *forward-scatter* on the irregular Voronoi mesh
(`moisture.py:184`, `moisture = bincount(indices, carry[src]*weights)`): a cell
fed by 4 upwind neighbours piles up, a cell fed by 0 goes dry, and that is pure
mesh-topology accident, not weather. The biome map faithfully reports the
artifact.

**End-to-end validation of the fix** (smooth precip proxy + province merge):

| Pipeline | components | singletons | flip | after merge < 2% land |
|---|---|---|---|---|
| Raw precip (today) | 650 | 269 | 0.435 | 21 provinces, ice_sheet 19% |
| Smooth precip | 183 | 21 | 0.262 | 19 biomes, 23 provinces, balanced |

Smoothing the precip *source* cuts single-cell biomes 269 → 21 (−92%); the
province merge then turns the coherent base into ~20 legible regions at flip
0.07. **Both steps are necessary; together they produce coherent, full-gamut,
balanced biomes.**

---

## 4. Framing decision: climate is the average; weather is a later layer

Climate here is the **long-term mean** state. Seasons and storms are a separate
future **weather** system that will consume these fields as baselines (redesign
plan decision #6). Consequences that drive the whole design:

1. **Smoothness is correctness, not taste.** No physical process in a
   climatology makes one hillside's *mean* rainfall jump 0.07 from its
   neighbour's. The speckle is the field failing to be the average it claims to
   be. Fixing it is not "prettifying."
2. **No post-hoc biome smoothing.** Once climate *is* the spatial average,
   biomes read it directly. The current `smooth_biome_weights` band-aid
   (`biomes.py:106`) is retired (see §6).
3. **Transient variation lives in weather, not climate.** High-frequency wind
   turbulence is moved out of the climate baseline (§5.3). Treat the climate
   fields as a documented **socket** for the future weather system, the way
   `region_id` is a socket for provinces.

The "cold/arid bias" is therefore mostly **not a bug**: real planets have large
cold and dry expanses, and once biomes are *coherent* those become legible
frontier features (taiga, tundra, high desert) that the existing `savagery`,
leyline, and vulcanism systems already make interesting. The only genuine
calibration error is narrow — `contrast = 0.8` compresses the temperature range
toward the middle while lapse-rate pulls it down with nothing pushing back
up (§5.1).

---

## 5. Climate redesign

### 5.1 Reframe around explicit, physical parameters

Today temperature is an emergent accident of `cosine × contrast ×
temperate_bias − lapse + maritime`; its mean drifted cold by side effect.
Replace the free aesthetic knobs with **two semantic parameters** plus physical
calibration:

- **Climate centre** and **spread** become first-class. Interpret the torus as
  a **band of latitude**: the hot ring = an equator-like line, the cold ring =
  a pole-like line. "Spread" = *how much latitude the world spans* — a physical
  question, not a style dial.
- **Default span: full equator → pole** (most bottom-up; presets narrow/shift
  the window for thematic worlds — a temperate "Heartlands", a polar
  "Frostmarch"). **Open item (§10): sanity-check the default against a real
  render before finalising; if the default's first impression should be more
  inviting, centre the window warm while keeping the full range available.**
- **Lapse rate**: calibrate from a real atmospheric lapse rate (≈6.5 °C/km)
  mapped through the world's elevation scale to a target **snow line**, rather
  than a bare `0.3`. Variety then emerges from a physically grounded gradient;
  it is not separately dialled.
- Remove or repurpose `contrast`: range comes from the latitude window, not a
  compression factor that skews the mean.

### 5.2 Moisture transport — conservative finite-volume advection

Replace the forward-scatter with a **mass-conserving finite-volume** scheme on
the mesh:

- Advect as **flux across each Voronoi edge**:
  `flux(i→j) = upwind_moisture × (wind · edge_normal) × edge_length`. New
  moisture per cell = old + Σ inflow − Σ outflow. What leaves `i` through an
  edge is *exactly* what arrives at `j` — convergence/divergence lumps cancel
  instead of accumulating, so the field is smooth by construction.
- Add a **small physical eddy-diffusion term** (turbulent vapour mixing — a real
  climatological process currently missing). Calibrate it to remove residual
  graininess **without** erasing real rain shadows (§10).
- **Mesh geometry work**: store per-edge **length** and **outward normal** on
  `MeshGeometry` (reusable by any future field that flows or diffuses on the
  mesh).
- **Invariant test** this enables: global mass balance — total vapour =
  Σ evaporation − Σ rainfall (to tolerance). Auditable correctness, the
  first-principles guardrail.

*(Fallback only if FV's per-step cost or CFL stability ever bites: a
semi-Lagrangian backtrace — smooth and unconditionally stable, but only
approximately mass-conserving. Not needed for a ~30-pass offline generator.)*

### 5.3 Wind — climate baseline only

Climate wind = **prevailing zonal belts + low-frequency standing features
(monsoons, semi-permanent highs/lows — genuinely climatic) + terrain
deflection.** **Strip the high-frequency FBm `turbulence`** — gustiness is
weather and belongs to the future weather layer, not baked permanently into the
baseline. Keep only low-frequency variation so the field stays an average.

---

## 6. Biome redesign

Biomes **emerge** from the now-smooth climate; the model gets *simpler*, not
more elaborate.

- **Keep the 49-biome `BIOME_GRID` (7×7) as the single source of truth** — it is
  a core/model gameplay fact, unchanged.
- **Classify per-cell directly on the climate average.** Keep the IDW soft
  weights for ecotone detail. **Delete the `smooth_biome_weights` output
  band-aid** — once §5.2 lands, the input is already an average, so smoothing
  the output is the "outside knob" we are explicitly avoiding. Re-measure flip
  rate after FV; only revisit if the data demands.
- **Variety is emergent**, set by the latitude window (§5.1), not a chosen
  biome count. Full gamut yields ~19 effective biomes, balanced (top ~14–17%).

---

## 7. Provinces — `region_id` derived *from* biomes

Provinces are an **output** of the biome layer, not a separate input (bottom-up;
matches the intended mental model):

```
physics → climate (average) → coherent biomes → region_id = connected
same-biome components, merged up to a minimum size
```

- Compute connected components of the dominant biome over land (BFS on the CSR
  adjacency — same pattern as landmass labelling).
- **Merge components below a minimum fraction of land into their largest
  neighbouring biome.** This is the **legibility knob** and is cleanly separate
  from climate spread (which sets *variety*): ~1% → ~40 provinces, **~2% →
  ~20–23 provinces** (recommended default). No artificial polygonal seams,
  because the base biome field is already coherent.
- Fill the `region_id` column (currently all `-1`) with the merged province id.
  Ships on `GridFields` as first-class data for future gameplay (naming,
  quests, politics).

---

## 8. Validation & guardrails

The only reason this round's defect was found (and three wrong guesses
discarded) is that we **measured**. Bake the instruments in. Strictness split by
nature of the property (consistent with the plan's "no golden-image tests"):

**Hard invariant tests** (physically definite — fail CI):
- FV **mass balance**: Σ evaporation − Σ rainfall = total vapour, to tolerance.
- Determinism: same seed → identical output.
- Field ranges: temperature/precipitation ∈ [0,1]; wind unit-length where
  magnitude > 0; biome weight rows sum to 1 on land.

**Soft reported metrics** (taste — printed by `census.py`, human-judged):
- **Biome single-cell count** and **component count** (the most diagnostic —
  269 → 21 singletons is the FV payoff).
- Adjacent-land **biome flip rate**.
- **Biome distribution** (count of effective biomes + top-share / entropy) — is
  it varied *and* balanced rather than a 49-way tie or a monoculture?
- **Province count** (post-merge) and largest-province share.
- **Climate centre & spread** actually achieved (did we land where we aimed?).
- **Livability %** (land in comfortable temp/precip ranges) — a fun/danger dial.

These extend `scripts/census.py`, the existing "regression eyeball."

---

## 9. Phasing

| Phase | Deliverable |
|---|---|
| 0 | Mesh edge geometry (length + outward normal); census gains the new soft metrics (singletons, components, flip rate, distribution) so we can see movement. No behaviour change yet. |
| 1 | Finite-volume moisture advection + eddy diffusion; mass-balance invariant test; viewer precip layer. Expect singletons to collapse (≈269 → ~20). |
| 2 | Wind: strip HF turbulence, keep prevailing + low-freq standing + deflection. |
| 3 | Climate reframe: latitude-window centre/spread params, physical lapse calibration, retire `contrast` skew, default full-gamut span. Tune against renders. |
| 4 | Biomes: delete `smooth_biome_weights`; classify on the average; confirm coherence by measurement. |
| 5 | Provinces: connected-component merge → fill `region_id`; province metrics in census. |
| 6 | Final tuning pass against the soft metrics; sanity-check the default span render (§10); docs. |

---

## 10. Open items to sanity-check during implementation

1. **Default latitude span** — full equator→pole is provisional. Look at a real
   default render; if the first impression must be inviting, centre warm while
   keeping the full range as a capability.
2. **Eddy-diffusion coefficient** — must smooth residual graininess *without*
   washing out real rain shadows. Calibrate by eye + the flip/component metrics;
   the acceptance test is "the rain shadow behind the biggest range survives."
3. **FV flip-rate floor** — smoothing alone bottomed out near flip 0.26 in the
   proxy; confirm FV reaches similar, and rely on the province merge (§7) for
   final legibility rather than over-diffusing the climate.
4. **Lapse / snow-line target** — pick the elevation→temperature scale against a
   desired snow line so peaks read cold without dragging the whole world cold.

---

## 11. Decision log (interview)

| # | Decision |
|---|----------|
| 1 | Scope = climate + ecology only; terrain/hydrology verified sane on HEAD. |
| 2 | Deep, first-principles changes preferred over outside-knob tweaks; no surface band-aids. |
| 3 | Climate = long-term average; weather (seasons/storms) is a separate later layer consuming these baselines. Smoothness is a correctness property. |
| 4 | Speckle root cause = non-conservative forward-scatter advection on the irregular mesh (measured). |
| 5 | Fix advection with **conservative finite-volume flux across Voronoi edges + physical eddy diffusion**. |
| 6 | Reframe climate around **explicit centre + spread**; torus interpreted as a latitude band; physical lapse calibration. |
| 7 | **Default span = full equator→pole** (most bottom-up; presets narrow). Provisional — sanity-check render. |
| 8 | Cold/dry land is realistic, not a bug, once biomes are coherent. |
| 9 | Climate wind = prevailing belts + low-frequency standing features + deflection; **strip HF turbulence** (it's weather). |
| 10 | Keep the 49-biome grid; classify directly on the average; **delete the output-smoothing band-aid**. |
| 11 | `region_id` provinces = **connected same-biome components, min-size merged** — derived *from* biomes. Merge threshold is the legibility knob (~2% land → ~20 provinces). |
| 12 | Guardrails: **hard invariants** (mass balance, determinism, ranges) + **soft census metrics** (singletons, components, flip rate, distribution, provinces, livability, achieved centre/spread). |
