# Worldgen Magic Redesign — Mana Hydrology

Status: **implemented.** Steps 0–7 are done; see "Implementation notes" at the
bottom for where the build differs from this map. The body below is the design
it was built to.

Scope: `src/worldgen` magic only. Replaces the leyline/nexus **drawing** model
(score nexuses → MST + loop edges → distance-falloff rasterize) with a
**simulation** model that mirrors the water subsystem: magic flows over a
potential and accumulates into dendritic veins, exactly as discharge accumulates
into rivers. This is the "climate baseline" for a future runtime magical-weather
layer (out of scope here). Everything below obeys
`docs/worldgen-guide/CONVENTIONS.md`; when this doc and that file disagree on
*style*, that file wins.

---

## 0. Decisions (interview log)

| # | Decision |
|---|----------|
| 1 | **Drop the pure↔corrupt valence axis.** It contradicts `docs/domains.md`, where corruption is a *direction a mark cuts on a trunk's aspect*, not a world-axis. `magic_valence` / `nexus_valence` / `FIELD_VALENCE` / `purity` / `valence_frequency` are removed. `magic_strength` and `magic_channels` survive. **(done in code)** |
| 2 | **Magic is a climate-style emergent simulation**, not authored rasterization. It is the slow-varying *baseline* a future magical-"weather" system rides on, so it must be broad, coherent, and causally legible. |
| 3 | **Leylines are dendritic "spider-veins," generated like rivers** (receiver-forest flow + accumulation), never straight MST chords. |
| 4 | **Topology is a "magnetic field": poles, not a drawn graph.** Magic flows from sources (+) to sinks (−). |
| 5 | **Poles come from a continuous low-frequency "ley-mantle" field** — magic's own deep geography, rock-independent. Its **maxima are sources (+)**, **minima are sinks (−)**; polarity is intrinsic, charge magnitude is the extremum's prominence. Nexuses are the field's *enumerated extrema*, not placed points. |
| 6 | **Veins get their dendritic detail from the rock "bones."** A smooth ley-mantle alone yields broad flows; the fine, linear structure of faults/ridges carves the branching. `combined_potential = ley_mantle − bones_weight · structural_bones` (bones are *troughs* the flow concentrates into). |
| 7 | **Channels (corpus/mens/anima) are source-flavored and flow-mixed.** Headwaters draw a channel identity from three low-frequency noise fields (clustered "corpus/mens/anima-lands"); channels advect downstream and blend at confluences, flow-weighted — a vein's flavor is the discharge-weighted mix of its sources, like tributaries mixing water. |
| 8 | **Magic mirrors the `water/` subsystem byte-for-byte** ("hydrology of mana"). This is the most robust path: it reuses the battle-tested priority-flood / receiver-forest / accumulation / path-labeling machinery, matches how the rest of worldgen is built, and lets a future "sockets" refactor unify water + magic for free. |
| 9 | **Emission is source-weighted, not uniform** — water accumulates `precipitation`, not `1.0`, so magic accumulates a `source_emission` field (the ley-mantle's "+" regions are mana's rainfall). |

---

## 1. The model

Three layers, cleanly separated:

* **Where magic comes from** — the **ley-mantle**, magic's own low-frequency
  deep field, independent of the rock. Its highs are wellsprings (sources, +),
  its lows are drains (sinks, −).
* **How magic threads the world** — the rock **bones** (faults + ridges) carve
  fine troughs into the potential, so the flow branches along the world's
  fractures. Veins look geological without the poles being tied to terrain.
* **What flows** — a **channel** triad (corpus/mens/anima) seeded at headwaters
  and mixed downstream, plus the accumulated **strength** itself.

Magic then *is* a drainage network: sources are headwater peaks, sinks are
mouths, veins are the high-accumulation channels between them, and the
background floor is un-accumulated ambient emission.

### Mirror map (the contract with `water/`)

| Water | Magic |
|---|---|
| `elevation` / `z_route` | `combined_potential` |
| `priority_flood`, `compute_receivers`, `accumulate_drainage` (`terrain/routing.py`) | **reused as-is** |
| `precipitation` (emission weight) | `source_emission` (ley-mantle "+" regions) |
| `accumulate_discharge` → `discharge` | `accumulate_strength` → `magic_strength` |
| `classify_rivers` / `extract_rivers` → `River` | `classify_veins` / `extract_veins` → `Vein` |
| `extract_lakes` → `Lake` (basins) | `extract_nexuses` → `Nexus` (potential extrema / poles) |
| `compute_flow` → `flow_u/v/speed` | `compute_magic_flow` → `magic_flow_u/v/speed` (mana currents) |
| `river_id` / `lake_id` tile columns | `vein_id` / `nexus_id` tile columns |
| — (no analog) | `magic_channels` (a transported 3-vector tracer) |

---

## 2. Files

```
src/worldgen/magic/
    potential.py   # pure: build_ley_mantle, build_structural_bones, combine_potential
    accumulate.py  # pure: accumulate_strength (mirror accumulate_discharge)
    channels.py    # pure: seed_source_channels, mix_channels (downstream blend)
    veins.py       # pure: classify_veins, extract_veins   (mirror water/rivers.py)
    nexuses.py     # pure: extract_nexuses                 (mirror water/lakes.py)
    flow.py        # pure: compute_magic_flow              (mirror water/flow.py)
src/worldgen/stages/
    magic_potential.py   # MagicPotentialStage
    magic.py             # MagicStage  (accumulate + channels + veins + nexuses + flow)
src/worldgen/features.py # replace LeylineNetwork with Vein + Nexus dataclasses
```

`magic/savagery.py` is **unrelated** (savagery is its own thing) — leave it.
Delete the old drawing modules: `magic/nexus.py`, `magic/web.py`,
`magic/aspects.py`, `magic/fields.py` (the rasterizer), and `stages/leylines.py`.

> Granularity note: water splits Discharge/Rivers/Lakes/Flow into four stages.
> Magic *may* mirror that 1:1, but the accumulation, channel-mix, vein/nexus
> extraction, and flow all share one receiver forest, so a single `MagicStage`
> after `MagicPotentialStage` is acceptable and keeps the seam count down. Pick
> the split that reads cleanest; the pure functions are the same either way.

---

## 3. Algorithm

### 3.1 Potential (`magic/potential.py`, `MagicPotentialStage`)

```python
def build_ley_mantle(
    *, geometry: MeshGeometry, mantle_noise: FractalField, cfg: MagicConfig
) -> Float64Array:
    """Low-frequency FBm 'ley-mantle' over the mesh, normalized to ~[-1, 1]."""

def build_structural_bones(
    *,
    geometry: MeshGeometry,
    facts: BoundaryFacts,
    slope: Float64Array,
    cfg: MagicConfig,
) -> Float64Array:
    """Fine, linear rock structure in [0, 1]: fault stress + ridge lines.

    bones = norm( bones_boundary_weight · (convergence + divergence)
                  + bones_ridge_weight · ridge(slope) ), lightly smoothed.
    """

def combine_potential(
    *, ley_mantle: Float64Array, bones: Float64Array, cfg: MagicConfig
) -> Float64Array:
    """combined = ley_mantle − bones_weight · bones (bones carve troughs)."""
```

* `mantle_noise` from `ctx.noise_for("ley_mantle")` / `FIELD_LEY_MANTLE`, very
  low `cfg.ley_mantle_frequency` (≈1.0–1.5) so polarity regions are broad.
* `facts` is `ctx.boundary_facts` (already produced by `BoundaryClassifyStage`);
  `slope` is the finalized `ctx.fields.slope`. Both exist by this point.
* `ridge(slope)` is a fine high-slope/ridge-line signal; keep it cheap (a slope
  percentile mask or a small Laplacian-of-elevation), config-weighted.
* Stash `combined_potential` on the context as a mesh intermediate for the
  viewer (like `z_route`); it need not bake to the grid.

### 3.2 Source emission + routing

```python
source_emission = np.clip(ley_mantle - ley_mantle.mean(), 0.0, None)   # "+" regions = mana rainfall
source_emission += cfg.ambient_floor                                    # so dead zones still flicker
```

Route over `combined_potential` with the **existing** helpers:

```python
potential_routed = priority_flood(geometry=..., z=combined_potential, ...)
receiver = compute_receivers(geometry=..., z_route=potential_routed, ...)
```

The − poles (minima) are the legitimate terminals (mouths); priority-flood only
guarantees a valid downhill receiver and deterministic flat-tie handling.

### 3.3 Strength (`magic/accumulate.py`)

```python
def accumulate_strength(
    *, receiver: Int32Array, potential_routed: Float64Array, source_emission: Float64Array
) -> Float64Array:
    """Accumulate source emission down the receiver forest (mirror accumulate_discharge)."""
```

Body is `accumulate_discharge` with `precipitation → source_emission` and no
land-masking (magic exists at sea too). Then normalize like discharge does in
the viewer — log-compress and scale to `[0, 1]`:

```python
magic_strength = clip( log1p(accum) / log1p(accum.max()), 0, 1 )
```

### 3.4 Channels (`magic/channels.py`)

```python
def seed_source_channels(
    *, geometry, corpus_noise, mens_noise, anima_noise, cfg
) -> Float64Array:
    """Per-cell headwater channel identity (n, 3): normalized low-freq noise triad."""

def mix_channels(
    *, receiver, potential_routed, source_emission, source_channels, magic_strength, cfg
) -> Float64Array:
    """Flow-weighted downstream blend of channel identities → per-cell (n, 3).

    Carry (flow, flow · channel) down the same topological order as strength;
    cell channel = Σ(flowᵢ·chanᵢ)/Σ(flowᵢ). Fade toward uniform ⅓ each where
    magic_strength is near the floor (weak magic has no opinion).
    """
```

Three independent noise fields (`FIELD_CHANNEL_CORPUS/MENS/ANIMA`) keep the
triad decorrelated; low frequency makes "corpus/mens/anima-lands." The mix is
one extra O(n) topological pass — reuse the strength ordering.

### 3.5 Veins (`magic/veins.py`) — mirror `water/rivers.py`

```python
def classify_veins(*, magic_strength, cfg) -> BoolArray:
    """Vein cells = magic_strength ≥ cfg.vein_percentile threshold."""

def extract_veins(*, geometry, receiver, magic_strength, magic_channels, nexuses, cfg) -> list[Vein]:
    """Label paths through the receiver forest: source headwater → sink pole.

    Mirror extract_rivers — at confluences the larger-strength inflow keeps the
    vein identity, smaller ones record tributary_of.
    """
```

### 3.6 Nexuses (`magic/nexuses.py`) — mirror `water/lakes.py`

```python
def extract_nexuses(*, geometry, combined_potential, ley_mantle, source_channels, cfg) -> list[Nexus]:
    """Enumerate salient extrema of the potential as poles.

    Maxima (prominence ≥ cfg.nexus_prominence) → SOURCE (+); minima → SINK (−).
    Charge = prominence; channel identity = source_channels at the cell.
    """
```

### 3.7 Magic flow (`magic/flow.py`) — mirror `water/flow.py`

Per-cell unit direction toward `receiver` and a stylized speed
`∝ magic_strength^a · slope(potential)^b`, normalized `[0,1]`. These
`magic_flow_u/v/speed` fields are the "mana currents" the future weather layer
consumes.

---

## 4. Output objects (`features.py`)

Replace `LeylineNetwork` with two River/Lake-shaped dataclasses:

```python
class NexusPolarity(IntEnum):
    SOURCE = 1    # ley-mantle maximum, magic wells up
    SINK = -1     # ley-mantle minimum, magic drains

@dataclass
class Nexus:
    id: int                      # matches nexus_id
    cell: int                    # mesh cell of the pole
    polarity: NexusPolarity
    charge: float                # [0,1] prominence of the extremum
    channels: Float64Array       # (3,) corpus/mens/anima identity

@dataclass
class Vein:
    id: int                      # matches vein_id
    cells: list[int]             # source → mouth, contiguous
    strength: Float64Array       # per-cell, len(cells)
    channels: Float64Array       # (len(cells), 3)
    source_nexus: int            # nexus id at the headwater
    mouth_nexus: int | None      # sink nexus id, or None
    tributary_of: int | None     # vein id this joins; None for trunks
```

`WorldData` swaps `leylines: LeylineNetwork` for `veins: list[Vein]` and
`nexuses: list[Nexus]` (mesh-cell coords; tile lookup via the id columns).

---

## 5. Fields, config, noise

**Fields** — add to **both** `MeshFields` and `GridFields` (`fields.py`); keep
`magic_strength` and `magic_channels`:

```python
magic_flow_u: Float64Array | None = ...        # unit mana-current x
magic_flow_v: Float64Array | None = ...        # unit mana-current y
magic_flow_speed: Float64Array | None = ...    # [0,1] stylized current speed
is_vein: BoolArray | None = ...                # tile carries a vein
vein_id: Int32Array | None = ...               # Vein id; -1 = none
is_nexus: BoolArray | None = ...               # tile is a nexus pole
nexus_id: Int32Array | None = ...              # Nexus id; -1 = none
```

**Config** — replace `LeylineConfig` with `MagicConfig` (delete the old knobs:
`count`, `min_spacing`, `peak/lake/confluence/volcano` bonuses, `edge_k`,
`extra_loops`, `line_reach`, `line_strength`, `nexus_reach/boost`, `idw_*`,
`score_*`, `channel_purity`, `floor_*`):

```python
@dataclass
class MagicConfig:
    """Mana hydrology: ley-mantle, rock coupling, emission, channels, veins."""
    ley_mantle_frequency: float = 1.2     # Low → broad source/sink regions
    ley_mantle_octaves: int = 3
    bones_weight: float = 0.6             # Rock coupling: how hard faults/ridges carve troughs
    bones_boundary_weight: float = 1.0    # Fault stress (convergence+divergence) share of bones
    bones_ridge_weight: float = 0.5       # Ridge-line share of bones
    bones_smoothing: int = 1              # Laplacian passes on bones
    ambient_floor: float = 0.05           # Uniform emission so dead zones flicker
    channel_frequency: float = 1.5        # Per-channel noise freq (clustered flavor regions)
    nexus_prominence: float = 0.15        # Min extremum prominence to enumerate a pole
    vein_percentile: float = 90.0         # Strength percentile that counts as a vein
    flow_strength_exp: float = 0.5        # Speed ∝ strength^this
    flow_slope_exp: float = 0.5           # Speed ∝ potential-slope^this
```

Register `magic: MagicConfig` on `WorldgenConfig`. Rebuild presets in the new
vocabulary (`wildlands` already lost its `purity` knob in step 0).

**Noise** — append to `noise/rng.py` (slot 9 stays a retired gap from step 0):

```python
FIELD_LEY_MANTLE: int = 11
FIELD_CHANNEL_CORPUS: int = 12
FIELD_CHANNEL_MENS: int = 13
FIELD_CHANNEL_ANIMA: int = 14
```

---

## 6. Pipeline, determinism, viewer, tests

**Pipeline** (`pipeline.py::_build_stages`) — replace `LeylinesStage()` with the
two magic stages, same slot (after Savagery, before Biomes):

```
... → Savagery → MagicPotential → Magic → Biomes → Regions
```

`MagicPotential` needs `boundary_facts` (early) + finalized `slope` (after
finalize) — both available by Savagery's point.

**Determinism** (per CONVENTIONS §9):
* All noise via `ctx.noise_for(...)` instances; new `FIELD_*` constants.
* Reuse the exact `priority_flood` / `compute_receivers` ordering — its tie
  breaks are already deterministic.
* Strength and channel accumulation run in one shared highest→lowest
  topological order; each donor completes before its receiver (single visit, no
  double-buffer needed — same argument as `accumulate_discharge`).
* Nexus/vein extraction sort candidates by (value, cell id).

**Viewer** (`scripts/worldgen_render.py`, CONVENTIONS §14): drop the removed
`MAGIC_VALENCE` layer (done). Re-point `MAGIC_STRENGTH`/`MAGIC_CHANNELS` at the
new fields, and add: `LEY_POTENTIAL` (debug, diverging palette), `VEINS`
(like the rivers layer), `NEXUSES` (poles colored by polarity, sized by charge),
`MAGIC_FLOW` (hue=direction, value=speed).

**Tests** (`test/worldgen/`, seed-parameterized):
* determinism: whole pipeline identical twice, incl. `Vein`/`Nexus` lists.
* `magic_strength ∈ [0,1]`; `magic_channels` rows sum to 1 (≈⅓ each where weak).
* every vein terminates at a SINK nexus or the map edge of a basin — the magic
  analog of "every river reaches ocean/lake."
* source nexuses are potential maxima, sinks are minima.
* torus continuity across both wrap seams.

---

## 7. Phasing

| Step | Deliverable |
|---|---|
| 0 | **(done)** Drop valence axis; tests green, strength/channels bit-identical. |
| 1 | `MagicConfig`, `FIELD_*`, ley-mantle + bones + `combine_potential`; `LEY_POTENTIAL` debug layer. |
| 2 | Source emission + routing + `accumulate_strength` → `magic_strength`; strength layer. |
| 3 | `seed_source_channels` + `mix_channels` → `magic_channels`; channels layer. |
| 4 | `extract_veins` → `Vein` objects + `is_vein`/`vein_id`; veins layer. |
| 5 | `extract_nexuses` → `Nexus` objects + `is_nexus`/`nexus_id`; nexuses layer. |
| 6 | `compute_magic_flow` → `magic_flow_*`; flow layer. |
| 7 | Swap `WorldData`/pipeline/features; delete old drawing modules; presets, full tests, README/glossary pass. |

Each step ends runnable and visible in the viewer.

---

## 7b. Implementation notes & divergences

What shipped, and where it differs from the map above:

- **One `MagicStage`, not two.** The doc allowed either; the build uses a single
  `stages/magic.py` that calls the pure functions in sequence
  (`potential → route → accumulate → channels → nexuses → veins → flow`). There is
  no separate `MagicPotentialStage`.
- **Pure functions** live in `magic/{potential,accumulate,channels,veins,nexuses,
  flow}.py`; `magic/savagery.py` is untouched. The old drawing modules
  (`magic/{nexus,web,aspects,fields}.py`, `stages/leylines.py`) are deleted.
- **`combined_potential` is stashed on `ctx.magic_potential`** (a mesh
  intermediate) so the nexus-polarity test (and a future viewer debug layer) can
  read it. The `LEY_POTENTIAL` debug viewer layer itself was not added (it needs
  mesh-intermediate baking); the shipped magic layers are `VEINS`, `NEXUSES`, and
  `MAGIC_FLOW` (plus the existing strength/channels), all from grid fields.
- **Routing base** = the lowest `base_fraction` percentile of `combined_potential`
  (via `argpartition`), mirroring `DischargeStage` exactly, rather than
  pre-identifying sink nexuses.
- **Nexus extraction** finds strict local extrema, max-normalizes prominence to a
  `[0,1]` charge, thresholds by `nexus_prominence`, and greedy-spaces by charge.
  Counts scale with mesh resolution (≈tens at debug scale); tune via
  `nexus_prominence` / `nexus_min_spacing`.
- **Tests:** the "every vein terminates at a sink" invariant was replaced by two
  more robust ones — `test_nexus_polarity_matches_extrema` (sources are strict
  maxima of `magic_potential`, sinks strict minima) and `test_veins_are_high_strength`
  (vein cells are exactly those above the percentile cutoff). 269 worldgen tests
  pass; ruff clean.

---

## 8. Deferred (separate round)

The generic **Feature/Area "sockets"** substrate and **deletion of the Region
tier** were interviewed at a high level and deliberately deferred. Key landing
points for that round: `River`/`Lake`/`Volcano`/`Vein`/`Nexus` are all "Features"
(crisp objects + id columns); `temperature`/`precipitation`/`savagery`/
`magic_strength`/`magic_channels` are all "Areas" (per-cell fields). Because this
magic round is built as a water mirror, water and magic already share the
Feature shape, so the eventual unification absorbs both at once.
