# Worldgen Ocean Currents Plan

Status: **implemented.** A guide for adding Gulf-Stream-style ocean-current
warming to the climate stack. Scope: `src/worldgen` climate phase plus its
fields/config/validation surface. See "Implementation notes" at the bottom for
what shipped and where it differed from this map.

This was parked as out-of-scope item #10 in `worldgen-sanity-plan.md`
("second-order; circulation sim was ruled out"). We are now building it — but
**not** as a circulation sim. The mechanism below is a wind-advected
sea-surface-temperature field that leans into the torus geometry rather than
mimicking Earth.

---

## 0. The standard (inherited)

Same as the sanity plan: **causal plausibility in service of legibility**, on a
torus that is **one whole planet**, emitting **climatic normals** (not weather).
Two inherited commitments shape every decision here:

- **No Coriolis on a torus** (decision #7). Belt/current *directions* are
  authored from latitude + geometry, never derived from rotation.
- **Climate-not-weather** (decision #4). We emit long-term averages and
  *preserve the drivers* (latitude, continentality, aridity) for a future
  weather layer. We do not bake transient state.

---

## 1. Decisions (interview log)

| # | Decision |
|---|----------|
| 1 | **Intent:** full **SST + moisture coupling** — warm *and* cold currents, feeding both temperature and precipitation. |
| 2 | **Mechanism:** **wind-advected SST.** Seed from the latitude baseline, advect heat along the existing prevailing-wind field, relax to baseline. Reuse moisture's downwind-fan CSR machinery. No circulation/gyre solver. |
| 3 | **Framing — lean into the torus.** Author currents as honest *toroidal* circulation: **circumpolar zonal bands** (x wraps → every all-ocean band is an unbroken current) + **continent-deflected gyres**. The warm-coast/cold-coast asymmetry emerges from wind meridional sign + continent geometry — **no faked Coriolis / western-margin fudge.** The strangeness (a band of ocean ringing the world at one temperature; one shared polar mixing ring at the y-seam) is embraced as deliberate. |
| 4 | **Pipeline reorder.** New climate order: **Insolation → Wind → OceanCurrent(SST) → Temperature → Moisture.** Wind has no temperature dependency, so it moves ahead of Temperature safely. |
| 5 | **Dedicated stage.** `OceanCurrentStage` writes an inspectable absolute `sst` field; Temperature and Moisture consume it. (Not folded into Temperature.) |
| 6 | **Absolute SST**, not an anomaly layer. SST = ocean latitude baseline, advected + relaxed. Temperature's maritime term moderates toward **real SST** (upgrading today's `insolation`-as-sea-temp proxy); evaporation reads SST directly. The current's effect is implicitly `SST − baseline`. |
| 7 | **Decay is physical, not a knob.** SST relaxes toward radiative-equilibrium baseline at the **air–sea thermal relaxation rate** (decay length ≈ advection speed ÷ heat-exchange rate). A physical constant like `lapse_rate`, not a shape fudge. |
| 8 | **Coupling depth: one-directional + transitive only.** SST → temperature (maritime) and SST → moisture (evaporation). Biomes/savagery/rivers inherit transitively. **No SST → wind** (that is a cycle and is weather, not climate). **No SST → ITCZ shift** — with wind held fixed there is no first-principles mechanism to bend the rain belt, so the "shift knob" was rejected as unphysical. Current-driven rain still happens, *physically*, via evaporation ∝ SST. |
| 9 | **Coast behavior: ocean-only advection graph + enforced no-normal-flow boundary condition.** Heat advects over ocean→ocean edges only (land is a barrier → isolated thermal basins for free). When a current meets a coast its direction is **projected onto the coastline tangent** so it runs *along* the shore (mass conservation, fully enforced — not a tuning knob). This produces coherent boundary-current ribbons and the legible warm/cold coast pair. |
| 10 | **Maritime sampling: upwind / wind-borne ocean SST.** A coastal land cell moderates toward the temperature of the water the wind *actually crossed* (advect SST inland along wind, decaying over `coast_distance`), not its geometrically nearest ocean. Keeps the windward/leeward asymmetry sharp. |
| 11 | **SST is a shipped output field** — on `MeshFields` *and* `GridFields`, baked to the grid, surfaced in viewer/census. A future weather/sailing/fishing layer wants real sea temperature as a socket. |
| 12 | **Pressure: skipped.** Redundant with authored wind, no geostrophic meaning on a torus, drives nothing new in the normals; its independent meaning is moving weather systems. The weather layer can derive climatological pressure from `latitude` + `sst`. Logged as future work. |
| 13 | **Validation: full toroidal sanity suite** — hard invariants + toroidal-signature bands + SST/anomaly census layers (§7). |

---

## 2. Why not a circulation sim (the cost argument)

A "real" Gulf Stream is a **western-boundary current**, and western
intensification is a **Coriolis/β-effect** phenomenon. On a torus there is no
Coriolis. A Stommel-style gyre solver would therefore produce a symmetric,
centered gyre with **no** western intensification *unless* we hand-inject an
artificial `β(latitude)` — i.e. smuggle back the exact Coriolis the project
rejected, buried inside a PDE.

So a circulation sim (≈500–900 lines: irregular-mesh Laplacian assembly +
boundary conditions + sparse solve + stable velocity-field advection;
~0.5–3 s/world; determinism risk on convergence) **still cannot produce the
asymmetry that motivates it** without faking Coriolis. Wind-advection + the
enforced coastal boundary condition gets the legible payoff (warm/cold coast
pairs, coherent ribbons) at **~250 lines, ~50–150 ms/world**, fully
deterministic, and honest to the geometry. Decision: wind-advection.

---

## 3. The model (first-principles, knob-free)

Every term is a physical mechanism; there are **no shape-knobs** (the would-be
fudges — western-margin bias and ITCZ shift — were both eliminated).

### 3.1 Sea-surface temperature field `sst`

Defined on **ocean cells only**.

1. **Baseline.** `sst_baseline = insolation` over ocean (the latitude-derived
   radiative-equilibrium sea temperature). Land cells have no SST.
2. **Advection graph.** Build a CSR fan over **ocean→ocean edges only** from the
   prevailing wind, identical in spirit to `moisture.build_downwind` but
   restricted to the ocean subgraph. Build once.
3. **No-normal-flow boundary condition.** Before/while building the fan, where
   the wind would drive a cell's flow into land, **project the flow direction
   onto the local coastline tangent** (reuse the `deflect_wind` projection
   pattern, using a coast normal derived from the ocean/land mask gradient).
   Fully enforced. This is what turns "warm water piles at the windward coast"
   into "warm water runs *along* the coast" — the boundary-current ribbon.
4. **Advect + relax to steady state.** Iterate for `passes`:
   `sst ← (1 − relax)·advect(sst) + relax·sst_baseline`
   where `advect` carries heat with the current (scatter downwind / gather
   upwind on the ocean graph) and `relax` is the **air–sea thermal relaxation**
   fraction per pass (physical timescale, §1.7). Steady state: heat carried far
   from its source decays back toward the local baseline over the relaxation
   length; unbroken bands homogenize; landlocked seas equilibrate to their own
   local baseline.
5. **Bounded by construction.** Convex combination of advected values and
   baseline ⇒ no cell exceeds its warmest source (no runaway).

**Torus continuity:** all offsets use the existing `torus_delta`; the field
wraps seamlessly on both seams. The y-seam is the shared polar mixing ring —
meridional transport that reaches it is deliberately one pole.

### 3.2 Temperature integration (`climate/temperature.py`)

- **Ocean cells:** `temperature = sst` directly (SST already includes baseline +
  current anomaly; replaces today's `maritime_weight = 1` pull toward
  `insolation`).
- **Land cells:** unchanged base + lapse, then **maritime moderation toward
  wind-borne SST**: advect ocean SST inland along the wind, decaying over
  `coast_distance` (air relaxes toward the land's own value as it penetrates),
  and moderate `temperature` toward that maritime SST by
  `maritime_weight · maritime_strength`. This *replaces* moderating toward the
  cell's own `insolation`. A coast downwind of a warm current is mild; downwind
  of cold upwelling is cold.

### 3.3 Moisture integration (`climate/moisture.py`)

- Evaporation refill becomes `moisture[ocean] = evaporation · sst[ocean]`
  (Clausius–Clapeyron: warm water charges the air with more vapor). Replaces
  `temperature[ocean]`. Current-driven rain emerges *physically* — warm-current
  moisture advects downwind and rains out through the existing orographic/chill
  terms; cold currents suppress evaporation → coastal-desert tendency.
- **No change to the latitude rain belts.** `precip_belt` stays a pure latitude
  function (see §6 future work for why bending it would require SST→wind).

---

## 4. Pipeline & code changes

| File | Change | Rewrite vs edit |
|---|---|---|
| `pipeline.py` `_build_stages` | Reorder climate phase to `Insolation → Wind → OceanCurrent → Temperature → Moisture`; insert `OceanCurrentStage`. | Edit |
| `stages/ocean_current.py` | **New** stage: reads wind + latitude + is_land + insolation; writes `sst`. | New |
| `climate/ocean_current.py` | **New** module: ocean-only downwind fan w/ coastal BC, advect+relax loop. (~100 lines, mirrors `moisture.py`.) | New |
| `climate/temperature.py` | Ocean = SST; land maritime term moderates toward wind-borne SST instead of `insolation`. | Edit |
| `climate/moisture.py` | Evaporation reads `sst`; build the maritime/upwind SST helper (shared with temperature). | Edit |
| `stages/temperature.py`, `stages/moisture.py` | Thread `sst` (and wind, already present) through. | Edit |
| `fields.py` | Add `sst` to `MeshFields` **and** `GridFields`. | Edit |
| `config/worldgen_config.py` | Add `OceanCurrentConfig`; wire into `WorldgenConfig`. | Edit |
| `bake/grid.py` | Bake `sst` to the grid (generic `value[nearest]`). | Edit |
| viewer / `scripts/census.py` | Add `sst` layer + anomaly (`sst − insolation`) debug layer. | Edit |

### Proposed `OceanCurrentConfig` (starting defaults — eyeball-tune)

```python
@dataclass
class OceanCurrentConfig:
    """Wind-advected sea-surface temperature (toroidal currents)."""
    passes: int = 40              # advect+relax iterations to steady state
    relaxation: float = 0.05      # air–sea relaxation fraction per pass (physical
                                  # timescale; smaller = currents reach further)
    maritime_reach: float = 4.0   # inland decay of wind-borne SST onto land
                                  # (mirror of TemperatureConfig.maritime_reach)
```

`relaxation` and `passes` together set the **transport length** — how far a
current carries its anomaly before equilibrating. These are physical, not shape
fudges. Presets bias them later if desired (default: shared across presets).

---

## 5. Consequences to embrace (the torus showing through)

- **Longitudinally banded ecology.** A circumpolar warm band gives a continent
  uniformly mild coasts at *every* longitude → biomes band around the world at a
  latitude more strongly than on Earth. Expected; not a bug.
- **One shared polar sea.** Meridional warmth reaching the y-seam enters a single
  mixing ring (both poles are the same wrapped circle).
- **Isolated thermal basins.** Landlocked/enclosed seas equilibrate to their own
  local baseline (Mediterranean/Black-Sea flavor) — a free consequence of the
  ocean-only graph.

---

## 6. Out of scope / future work

- **Convergence-derived rain belts.** ~~The deepest first-principles rain model
  would derive the latitudinal rain structure from wind convergence...~~
  **Implemented** — see `docs/worldgen-convergence-rain-plan.md`. Rain is now a
  consequence of the wind field (signed convergence: rising air wets, subsidence
  dries), the authored Gaussian belt is retired by default, and it sets up
  seasonal ITCZ migration for the future weather layer.
- **SST → wind feedback (monsoons / ITCZ migration).** The only physical way to
  bend the rain belt by SST. Requires a wind↔SST cycle (iterate to convergence),
  breaks the staged acyclic pipeline, and is weather, not climate. Deferred.
- **Climatological pressure field.** Derivable from `latitude` + `sst` by the
  weather layer; not baked now (§1.12).
- **Ekman / surface-current angle.** Real surface currents flow ~45° off the
  wind (Coriolis). No Coriolis on a torus ⇒ current ≈ downwind. Not modeled.

---

## 7. Validation — full toroidal sanity suite

Extends `test/worldgen/test_plausibility.py` (seed-parameterized, production-ish
mesh). Two tiers.

### 7.1 Hard invariants (always true)

| Invariant | Assertion |
|---|---|
| Range | ocean `sst ∈ [0, 1]`. |
| Seam continuity | `sst` continuous across both torus seams (existing torus-continuity harness). |
| Bounded / no runaway | no ocean cell warmer than its warmest baseline source (convex-combination property). |
| **Perturb-not-erase** | the global equator→pole mean-SST gradient keeps its sign — currents nudge, never invert, the latitude gradient. |
| Determinism | identical `sst` for identical seed. |
| Coverage | `sst` defined on all ocean cells; land cells excluded/sentinel and never read by the maritime term. |

### 7.2 Toroidal-signature bands (prove it does the thing)

| Signature | Assertion (conservative thresholds — tune) |
|---|---|
| **Non-no-op** | a non-trivial share of coastal land cells differ from their no-current temperature by ≥ a meaningful margin. |
| **Warm/cold coast pair** | for a continent spanning a latitude band, its opposing coasts differ in temperature (coastal-temperature variance *within* a latitude band exceeds a floor). |
| **Circumpolar homogenization** | an all-ocean latitude band has **lower zonal SST variance** than a continent-broken band — the signature torus test. |
| **Maritime moderation holds** | coasts remain milder (smaller temperature departure from comfort) than interiors at the same latitude. |

### 7.3 Human eyeball

`scripts/census.py` + viewer gain an **`sst` layer** and an **anomaly layer
(`sst − insolation`)** so warm/cold currents and the circumpolar bands are
directly visible. No golden images.

---

## 8. Phasing

Each phase ends runnable and inspectable in the viewer.

| Phase | Deliverable |
|---|---|
| A | **Reorder + SST field.** Move Wind ahead of Temperature; add `OceanCurrentStage` + `climate/ocean_current.py` (ocean-only fan, coastal BC, advect+relax); add `sst` to fields, bake, viewer/anomaly layer. SST visible but not yet consumed. |
| B | **Temperature coupling.** Ocean = SST; land maritime term moderates toward wind-borne SST. Re-tune `lapse_rate` / `maritime_strength` if needed. |
| C | **Moisture coupling.** Evaporation reads SST. Confirm coastal-desert / wet-warm-coast tendencies; watch for double-counting against existing advection. |
| D | **Validation.** Hard invariants + toroidal-signature bands; census/viewer pass. Lock conservative thresholds. |
| E | **Docs.** Update `worldgen-sanity-plan.md` item #10 to "implemented (see this doc)"; note the longitudinal-banding consequence. |

**Preserve-the-drivers checkpoint (every phase):** `latitude`, `coast_distance`,
`precipitation`, and now `sst` remain on the output for the weather layer.

---

## 9. Implementation notes & divergences

What shipped, and where it diverged from the map above:

- **SST advection** landed as planned in `climate/ocean_current.py`: an
  **upwind-gather** formulation (each cell takes the weighted mean of its upwind
  neighbours' SST, normalized per receiver) rather than a downwind scatter — the
  two are equivalent for an intensive scalar, and the gather makes the
  relaxation blend (`relax·baseline + (1−relax)·gathered`) read directly. The
  **no-normal-flow boundary condition** is `_coast_projected_wind`: the coast
  normal is the mean unit offset toward land neighbours, and the onshore wind
  component is projected out before the ocean-only gather is built.
- **Maritime onshore SST** (`maritime_sst_onshore`) uses a *second*, all-cell
  gather on the **raw** wind (maritime air crosses coasts; water does not),
  propagating ocean SST inland for `≈3·maritime_reach` passes; the inland decay
  itself is still the temperature stage's `exp(−coast_distance/reach)` weight, so
  no new decay knob was added. `OceanCurrentConfig` ended up as just
  `{passes, relaxation}` (the design's `maritime_reach` field was dropped —
  reuse `TemperatureConfig.maritime_reach`).
- **Temperature** (`compute_temperature`) now takes `sst` + `maritime_sst`:
  coasts moderate toward `maritime_sst` (replacing the old `insolation` proxy)
  and ocean cells are overwritten to `sst` so the current is authoritative.
- **Moisture**: `transport_moisture` gained an `sst` parameter; the ocean
  evaporation refill is `evaporation · sst` (was `· temperature`). The chill
  term still reads `temperature`. No ITCZ shift (§6 future work).
- **Pipeline** reordered to `Insolation → Wind → OceanCurrent → Temperature →
  Moisture`; `sst` is on `MeshFields`/`GridFields` and bakes through the generic
  path. Viewer gained **Sea temperature** and **Current anomaly** (`sst −
  insolation`) layers.
- **Validation** (`test/worldgen/test_ocean_currents.py`): synthetic-mesh
  signature tests (zonal band adds no zonal variance beyond the baseline;
  meridional flow makes warm+cold anomalies; coastal BC deflects wind; bounded)
  plus pipeline invariants (range, land = baseline, perturb-not-erase across
  `|latitude|` bands, currents-not-a-no-op, determinism). The "circumpolar
  homogenization" band was reframed from "SST ≈ baseline" to "**within-band
  zonal variance ≤ the baseline's own**", because zonal advection on the
  irregular mesh slightly *meridionally* smooths band peaks — that shifts band
  means, not zonal uniformity, so comparing against the baseline is the honest
  test. Full suite: 232 worldgen tests green.
