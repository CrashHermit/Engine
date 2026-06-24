# Worldgen Sanity Plan

Status: **implemented (Phases A–F).** See "Implementation notes & divergences"
at the bottom for what shipped and where it differed from this map. A guide for
rebuilding the parts of the worldgen pipeline that produced implausible output,
so the world reads as a believable planet.

Scope: `src/worldgen` only. The pipeline is fully implemented (Phases 0–5); this
is a *correction* round, not a greenfield build. We keep the mesh/grid duality,
the staged pipeline, the typed dataclass-of-arrays layout, and the feature-object
model. We change specific algorithms and tighten the validation net.

---

## 0. The standard

**Causal plausibility in service of legibility.** Every field must look like it
came from a real process *and* read clearly to a player/GM at a glance. Physical
realism is the means; a legible, believable map is the end. When the two conflict,
legibility wins — but we don't reach for an unphysical shortcut until a physical
model has actually failed to read.

A single generated world is **a whole planet**: equator to both poles, multiple
continents, the full climate range. Every density/count judgment below is made at
planetary scale.

### The climate-not-weather principle (cross-cutting)

Everything this pipeline emits is a **climatic normal** — a long-term average that
a *future* weather system will perturb, not an instantaneous state:

- `precipitation` = mean annual precipitation, not "it is raining here now."
- `wind_*` = *prevailing* wind (the climatological average). This is exactly why
  authored zonal belts are correct: they *are* the normal.
- `temperature` = mean annual temperature.
- `discharge` = average flow.

Two consequences we honor everywhere:

1. **Fields stay smooth and stable.** Weather adds the variance on top; we do not
   bake transient detail into the baseline.
2. **Preserve the drivers, not just the means.** A future seasons/weather layer
   reconstructs seasonal and diurnal variation from *latitude* (seasonal swing
   grows toward the poles), *continentality* (`coast_distance` — interiors swing
   more than coasts), and *aridity* (`precipitation` — deserts swing hard
   day↔night). **Do not collapse these drivers away.** They are the socket the
   weather layer plugs into.

---

## 1. Decisions (interview log)

| # | Decision |
|---|----------|
| 1 | **Standard:** causal plausibility in service of legibility. |
| 2 | **Scale:** one world = one whole planet. |
| 3 | **Climate model:** **latitude-band climate on the torus.** Commit the semantic — the warm band *is* the equator (map center), the cold band at the y-wrap seam *is* the poles. Build the whole climate stack on real latitude. Keep the torus for seamless geography/movement. `bands = 1`. |
| 4 | **Climate-not-weather:** all fields are climatic normals; preserve the seasonality drivers (latitude, continentality, aridity) for the weather layer. |
| 5 | **Sea level:** **emergent land fraction** from a stable hypsometric datum, varying by seed, with a **removable config clamp** (default `[0.25, 0.70]`). No more exact land-fraction quota. |
| 6 | **Volcanoes:** keep the continuous `volcanism` field dense and physical; **cull discrete `Volcano` landmarks to iconic scale (~8–20/planet).** |
| 7 | **Wind:** **three-cell zonal belts** — tropical easterlies, mid-latitude westerlies, polar easterlies — derived from latitude, with a meridional component, FBm turbulence, and terrain deflection. Authored (no Coriolis on a torus), torus-periodic. |
| 8 | **Precipitation:** **latitude rain belts + moisture advection.** A latitudinal baseline (wet equatorial ITCZ, dry subtropical ~30° deserts, wet temperate, dry poles) with downwind advection and orographic rainout on top. |
| 9 | **Rivers:** **materialize major rivers, headwater-traced, with tributary networks.** Minor streams stay implicit in the continuous `discharge`/`receiver` field as the tier-2 socket. |
| 10 | **Biomes:** keep the 7×7 Whittaker `BIOME_GRID`. Variety is restored by the climate fix, not by changing the grid. **Seasonality is the planned 3rd axis, arriving with the weather layer.** |
| 11 | **Magic:** **decouple from the climate rings.** Drop the `ring_bonus` term; nexuses key only off terrain/hydrology/volcanism. Keep the rest of the leyline model; tune by eye. |
| 12 | **Savagery:** keep the geography blend; **leave the magic coupling at 0.** Savagery (physical/geographic danger) and `magic_valence` (corruption) are **orthogonal axes**; a future encounter/threat layer composes them. |
| 13 | **Validation:** **plausibility-band assertions** (parameterized tests) + census as the human eyeball. Beyond the existing contradiction-invariants. |
| 14 | **Mesh resolution:** unchanged (12k cells is adequate at planetary scale). |
| 15 | **Approach:** phased plan, with rewrite-vs-edit seams called out per stage. |

---

## 2. What's wrong today (census evidence)

From `scripts/census.py` on the current build:

- **Volcanoes everywhere.** 27–57 discrete `Volcano` objects per world (6–10
  calderas). Geologically absurd as *landmarks*. (The continuous field being dense
  along arcs is correct — only the discrete count is wrong.)
- **Rivers are stubs.** Longest river 9–20 cells on continents ~45–65 cells wide;
  3–4 cells in archipelago. They don't read as continent-spanning rivers.
- **Biomes skew cold/arid and fragment.** polar_desert / cold_desert / ice_sheet /
  badlands / sagebrush_steppe dominate; the top biome rarely breaks 8%. Only ~10
  of 49 biomes ever appear.
- **Land fraction is pinned.** 38% / 24% / 64% — identical across every seed in a
  preset, because sea level slides to hit a quota. Sea level isn't a datum.

Each has a single, identifiable cause, addressed below.

---

## 3. Climate rebuild (the keystone)

The cold/arid/fragmented biome mix is **downstream of a broken climate**, not a
biome-model problem. On a torus the y-axis wraps, so insolation must be periodic
in y — you inevitably get a hot band and a cold band. The fix is not to fight that
but to **commit the semantic** and build a real zonal climate on it.

### 3.1 Latitude field (replaces abstract insolation rings)

- Place the **equator at the map center**, the **poles at the y-wrap seam**. One
  full cosine cycle over `height` (`bands = 1`): warm at center, cold at the seam.
- The planet is mirror-symmetric N/S (a northern and a southern temperate belt,
  both leading to the same wrapped polar cap). This is Earth-like enough to read
  correctly; the wrap is invisible in play.
- Define a **`latitude` signal** in `[-1, 1]` (0 = equator, ±1 = pole) derived from
  y, *periodic in y*. Insolation becomes a function of `|latitude|`. Keep the field
  inspectable in the viewer.
- **Tune for a wide temperate zone.** Of 7 temperature bands, 3 are cold; the land
  must fall predominantly in MILD/WARM after this change. `temperate_bias` and
  contrast are the knobs; validate against the biome-diversity band (§8).

**Seam note (implementation):** the latitude signal and everything built on it must
be continuous across the y-wrap. The N–S (meridional) wind component must go to
zero at the band centers (equator and pole) so it's smooth across the seam.

*Rewrite seam:* `climate/insolation.py` is a **clean rewrite** — it currently emits
an abstract ring field; it should emit a latitude-derived insolation plus expose
the `latitude` signal. Rename intent from "rings" to "latitude" throughout.

### 3.2 Wind — three-cell zonal belts

Replace the half-zonal belt pattern with explicit Earth-like circulation, as a
function of latitude:

- **Zonal (E–W) component** by band: tropical **easterlies** (trade winds),
  mid-latitude **westerlies**, polar **easterlies**. Pure function of latitude;
  wraps trivially along x.
- **Meridional (N–S) component** with the Hadley/Ferrel/polar sense, **zero at each
  band center** (smooth across the seam).
- **FBm turbulence** and **terrain deflection** (steer around uphill gradients,
  channel through passes) on top — keep the existing deflection machinery.
- **No Coriolis** (a torus has no rotation axis): belt directions are *authored*
  per latitude band. This is consistent with the project's "authored wind"
  decision; it's causally motivated, not simulated.

*Rewrite seam:* `climate/wind.py` is a **clean rewrite** of the belt-direction
logic; keep the turbulence + deflection stages as edits.

### 3.3 Precipitation — latitude rain belts + advection

Keep evaporation → downwind advection → orographic/chill rainout, and add a
**latitudinal baseline** so Earth's wet/dry banding emerges reliably:

- **Wet equatorial belt** (rising air / ITCZ).
- **Dry subtropical "horse latitude" deserts** (~30°) — a circulation effect pure
  advection cannot produce; this is the main new term.
- **Wet temperate belt**, **dry poles**.
- Advection + orography modulate the baseline (rain shadows, wet windward coasts,
  dry interiors) — the **baseline is primary, advection is the local detail** (not
  the other way around).

This is the term that most directly cures the all-cold-desert skew.

*Rewrite seam:* `climate/moisture.py` is an **edit** — add the latitude baseline as
a new term feeding the existing advection loop; keep the saturating-curve
normalization.

### 3.4 Temperature

Keep `insolation − lapse + maritime moderation` (`climate/temperature.py`) — it's
sound. It now consumes the latitude-derived insolation. **Preserve `coast_distance`
on the output** (continentality is a weather-layer driver). Re-tune `lapse_rate`
and `maritime_*` after the new climate lands.

---

## 4. Sea level — emergent fraction

Replace the exact land-fraction quota with a **stable physical datum**:

- Set sea level from the **eroded elevation distribution (hypsometry)** — e.g. a
  fixed datum on the normalized height field — so a "wet" seed floods more and land
  fraction varies by seed.
- **Clamp** the resulting land fraction to a configurable range, default
  `land_fraction_clamp = (0.25, 0.70)`, to prevent all-ocean/all-land degenerates.
  **Widening to `(0.0, 1.0)` disables guardrails** — per-preset or globally — with
  no algorithm change. Presets bias the datum, not a hard quota.

*Rewrite seam:* `SeaLevelConfig` + the finalize sea-level cut is an **edit**:
replace the percentile-to-hit-quota with a datum-plus-clamp. Update presets to
express intent via the datum.

---

## 5. Volcano cull

The mechanisms (subduction arcs, hotspot drift chains, mid-ocean ridges) are
physically sound — **keep them and keep the continuous `volcanism` field dense**
(savagery and nexus placement read the field, and the Ring of Fire *should* be
densely volcanic).

Cull only the **discrete `Volcano` landmark objects** to iconic scale (~8–20/planet):
keep the most prominent breached edifices — active arc stratovolcanoes, hotspot
chain heads, the rare giant — and drop the rest. Verified consumers:

- `magic/savagery.py`, `magic/nexus.py` → read the **continuous field** (unaffected).
- `water/lakes.py` → caldera→crater-lake injection needs `has_caldera` volcanoes;
  ensure a few iconic ones carry calderas so crater lakes survive.
- `is_volcano` / `volcano_id` tile flags → viewer/census only.

*Rewrite seam:* `VolcanoesStage` (in `stages/vulcanism.py`) is an **edit** — tighten
the keep-rule (prominence threshold + per-chain cap) so the materialized set lands
in the iconic band. Tune `arc_volcano_spacing`, `max_per_chain`, `hotspot_count`,
`chain_length` downward.

---

## 6. Rivers — headwater tracing

The short-river cause is the **classification threshold**: `river_fraction = 0.05`
makes only the top 5% of land cells by discharge "river" cells, so a river is only
its high-discharge lower trunk — headwaters are clipped, truncating every river
from the top.

Fix: **trace each major river from a real headwater down to the sea.**

- Seed sources from the flow tree (`receiver`/`discharge`) at a **low** discharge
  threshold (a true headwater), not a top-percentile cut, so trunks span continents
  and tributaries branch. The existing `extract_rivers` trunk-identity + tributary
  logic is correct and stays.
- **Materialize major rivers only.** Minor streams stay implicit in the continuous
  `discharge`/`receiver` field — the **tier-2 socket**, recoverable deterministically
  whenever a consumer (the weather/runoff layer) wants them. Same pattern as the
  volcano field.
- Promotion to materialized minor-stream objects is a small additive change if a
  near-term need (drawn creeks, fordability) appears.

*Rewrite seam:* `water/rivers.py::classify_rivers` is an **edit** (change what
"river cell" means — headwater-reachable above a low threshold, rather than a top
percentile). `extract_rivers` is unchanged.

---

## 7. Ecology, magic, savagery (keep + re-tune)

### 7.1 Biomes
Keep the 7×7 Whittaker `BIOME_GRID` (the single source of truth). The variety
returns *for free* once the climate rebuild exercises the MILD/WARM/HOT rows the
land never reaches today. Re-tune `blend_sharpness` / `smoothing_*` after climate
lands. **Seasonality is the designed-in 3rd axis** (Mediterranean vs. monsoon vs.
oceanic), arriving with the weather layer — do not add it now.

### 7.2 Magic — decouple from climate
Drop the `ring_bonus` term in `magic/nexus.py` so nexus placement keys only off
**terrain/hydrology/volcanism** (peaks, lake outlets, confluences, volcanic ground)
+ noise. Rationale: "corruption gathers at the equator" is anti-causal; "magic pools
at dramatic places" reads. This also removes magic's only dependency on the climate
rebuild. Keep the nexus → MST web → clustered-valence → IDW-rasterize model; tune
`count`/`min_spacing`/valence `frequency`/`purity` by eye after everything else lands.
Remove `ring_bonus` from `LeylineConfig`. (`purity`'s "toward the poles" refers to
*valence* poles ±1 — unrelated, keep.)

### 7.3 Savagery — orthogonal to corruption
Keep the remoteness/harshness/ruggedness/volcanism blend. **Leave `magic_weight = 0`.**
Savagery = physical/geographic danger; `magic_valence` = corruption — **two
orthogonal axes**, preserving the 2×2 of region flavors (corrupt+savage,
corrupt+calm, pure+savage, pure+calm). A future encounter/threat layer composes
`total_threat = f(savagery, valence, …)`. **Document** that anything reading only
`savagery` sees geographic danger, not corruption.

---

## 8. Validation — prove it stays sane

Keep the existing contradiction-invariants (determinism, range contracts,
rivers-reach-sea, flow strictly downhill, weight rows sum to 1, torus continuity).
**Add plausibility-band assertions** as seed-parameterized tests — these catch
implausibility (the "50 volcanoes" / "all cold desert" class of regression) that
invariants miss:

| Metric | Sane band (starting point — tune) |
|---|---|
| Land fraction | within the active clamp (default 25–70%) |
| Discrete volcanoes | ~5–25 per planet |
| Calderas | ≤ ~⅓ of volcanoes |
| Biome diversity | ≥ N distinct biomes present; no single biome > X% of land |
| Temperate-land share | MILD+WARM dominate land (cold bands not majority) |
| Longest river | ≥ a continent-spanning cell count |
| Rivers reach sea | 100% terminate at ocean or an outlet-chained lake |

Keep `scripts/census.py` as the **human eyeball** and the regression-diff surface.
(No golden images; no full statistical harness this round.)

---

## 9. Phasing

Each phase ends with the pipeline runnable and inspectable in the viewer. Order is
by dependency; the climate rebuild is the keystone and comes first because the
biome mix, savagery harshness, and rain-fed rivers all depend on it.

| Phase | Deliverable | Rewrite vs edit |
|---|---|---|
| A | **Climate rebuild.** Latitude field + insolation; three-cell zonal wind; latitude rain belts into moisture; temperature re-tune. Viewer: latitude, wind belts, precip belts. | Rewrite `insolation.py`, `wind.py` belt logic; edit `moisture.py`, `temperature.py`. |
| B | **Sea-level emergence.** Datum + removable clamp; presets re-expressed via datum. | Edit `SeaLevelConfig` + finalize cut. |
| C | **Volcano cull.** Tighten keep-rule to iconic band; preserve caldera lakes. | Edit `VolcanoesStage` + `VulcanismConfig`. |
| D | **River headwater tracing.** Low-threshold source seeding; trunks to the sea. | Edit `classify_rivers`. |
| E | **Re-tune ecology/magic/savagery.** Biome blend/smoothing; drop `ring_bonus`; confirm savagery orthogonality. | Edit `biomes.py`, `nexus.py`/`LeylineConfig`; savagery unchanged. |
| F | **Plausibility-band tests + census pass.** Lock the bands; final docs pass. | New tests; doc edits. |

**Preserve-the-drivers checkpoint (do in every phase):** confirm `latitude`,
`coast_distance`, and `precipitation` remain on the output so the future weather
layer can derive seasonal/diurnal variation.

---

## 10. Out of scope (noted, not done)

- **Ocean-current warming** (Gulf-Stream-style) — ~~second-order; circulation sim was
  ruled out. Possible future climate refinement.~~ **Implemented** as a
  wind-advected sea-surface-temperature field (no circulation sim) that leans
  into the torus geometry — see `docs/worldgen-ocean-currents-plan.md`. One
  consequence to note: a circumpolar warm band gives a continent uniformly mild
  coasts at every longitude, so biomes band longitudinally more strongly than on
  Earth.
- **Seasonality / weather** — the future layer these baselines feed. Biome 3rd axis
  and tier-2 minor streams arrive with it.
- **Materialized minor-stream objects** — implicit in the `discharge` field until a
  consumer needs them.
- **`service/world.py` / persistence** — already known-broken against the new
  worldgen shape; its own round.

---

## 11. Implementation notes & divergences

What shipped (Phases A–F, each its own commit), and where it diverged from the
map above:

- **Climate (A)** landed as planned: a signed `latitude` field (equator at map
  center, poles at the wrap seam) on both `MeshFields` and `GridFields`;
  insolation from `|latitude|`; three-cell zonal wind (`-sin(3π|lat|)` zonal,
  toward-equator/pole meridional); latitude rain belts (Gaussian ITCZ +
  temperate bumps) × advection. Tuning to escape the over-arid regime
  (`precip_gamma=0.6`, wider belts) was needed; HYPER_ARID land dropped ~55% →
  ~24% and forests/jungles/savannas now dominate.
- **Sea level (B)** uses an **Otsu** threshold over the elevation histogram (the
  ocean/continent valley) as the datum — a clean, parameter-free choice not
  named in the plan. Land fraction is emergent (earthlike 35–51%, pangaea
  51–69%) inside a removable `land_fraction_clamp`.
- **Volcanoes (C):** the iconic cull is a **global prominence cap**
  (`max_volcanoes=18`) plus a lower `max_per_chain` and **dropping submarine-only
  anchors** — count fell from 27–57 to ~18. Calderas/crater-lakes preserved.
- **Rivers (D) — the big divergence.** The plan assumed rivers were clipped
  stubs and prescribed headwater re-tracing. Investigation showed rivers were
  **already continent-spanning at the production mesh** (earthlike 50/35/51,
  pangaea 55/71 cells); the "stubs" were a **census artifact** of running at
  3000 cells, too coarse for drainage to form. Lowering the discharge threshold
  only spawned hundreds of tiny stub-rivers. So **no river-algorithm change was
  made**; instead `CENSUS_CELLS` was raised (3000 → 6000) so the eyeball stops
  lying, and the continent-spanning guarantee became a full-resolution
  plausibility test.
- **Magic (E):** `ring_bonus` and its insolation read are gone; nexuses key only
  off terrain/hydrology/volcanism. **Savagery** turned out to never read
  magic/valence at all — already orthogonal — so the dead `magic_weight` knob
  was removed and the orthogonality documented. Biome `blend_sharpness`/
  `smoothing` were left as-is (the climate rebuild restored variety on its own).
- **Validation (F):** `test_plausibility.py` asserts the bands (land-in-clamp,
  volcanoes 3–25, caldera minority, ≥6 distinct land biomes & none >45%, cold
  land <55%, rivers present and ≥10 cells on a major landmass) across a few
  representative worlds at an 8k mesh. The `test_coasts_wetter_than_interiors`
  invariant was refined to compare *within* latitude bands (an equatorial
  interior is legitimately wetter than its subtropical coasts).
