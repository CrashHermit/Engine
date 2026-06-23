# Worldgen Vulcanism Plan

Status: **design (interview complete, pre-implementation).**

Scope: `src/worldgen` only. Adds volcanism to the existing terrain genesis —
volcanoes, volcanic arcs, hotspot island chains, and mid-ocean ridges — as a new
terrain contribution, a persistent field, and first-class feature objects. The
generator stays a pure function of `(seed, size, config)`; `WorldData` grows a
`volcanoes` list and three grid columns. Persistence (`service/world.py`,
`TileRepository`) remains out of scope and known-broken, as in the redesign.

This plan extends `worldgen-redesign-plan.md`; it does not restate it. Where the
two disagree, this document wins for anything volcanism-touching.

---

## 1. Decisions (interview log)

| # | Decision |
|---|----------|
| 1 | **Three mechanisms, all in.** Subduction arcs (convergent), hotspot plumes (interior), and rift/divergent volcanism. Each maps to a distinct landform family (arcs, chains, ridges) and reuses the existing plate machinery. |
| 2 | **Three representations, all in.** Volcanism (a) shapes elevation, (b) is a persistent scalar field on `MeshFields`/`GridFields`, and (c) ships as `Volcano` feature objects — mirroring how rivers/lakes already work. |
| 3 | **Terrain contribution runs before erosion**, so arcs/ridges/chains are dissected and drained causally (the engine's "causally consistent, not pretty" rule). A post-erosion crisp-cone/caldera pass is left as a **documented seam**, not built this round. |
| 4 | **Full subduction polarity.** The denser plate subducts; the arc forms on the *overriding* plate, offset from the trench. Ocean–continent → inland continental arc (Andes); ocean–ocean → offshore island arc (Japan); continent–continent → mountains, **no volcanism** (Himalaya). |
| 5 | **Hotspots emit drift-aligned decaying trails.** A fixed point; the host plate's drift stamps a line of volcanoes whose height decays down-trail (active head → seamounts/atolls below sea level). Placement biased to oceanic-plate interiors, with a knob for continental hotspots. |
| 6 | **Rift volcanism is type-split and reshapes terrain.** Oceanic divergent → a modest raised mid-ocean ridge (can breach as Iceland-style islands) replacing the pure depression. Continental divergent → keep the rift valley *and* add flanking volcanism + occasional rift volcanoes. |
| 7 | **`Volcano` carries kind, status, caldera flag, chain id.** Kind from mechanism (arc→stratovolcano, hotspot→shield, rift→fissure); status active/dormant/extinct; `has_caldera` forces a crater lake; `chain_id` groups arc/trail members. |
| 8 | **Coupling: savagery + magic nexuses only.** A volcanism weight in the savagery blend; a volcano bonus in nexus scoring. **No** geothermal climate term, **no** volcanic biome (the latter would break the `argmax == BIOME_GRID` invariant — volcanism stays an overlay field). |
| 9 | **Shared boundary classifier.** Extract `terrain/boundaries.py`: walk plate borders once, emit per-cell boundary facts (pair types, convergence/divergence, subduction polarity). `boundary_uplift.py` is refactored to consume it; the vulcanism stage consumes it too. Single source of truth. |
| 10 | **The volcanism field means present-day activity** [0,1], decaying with age/status — a hazard/heat signal, which is what savagery and nexuses actually want. Extinct seamounts and old eroded provinces read low. |
| 11 | **Presets tuned, no new preset.** archipelago = high (volcanic-origin islands), wildlands = high, earthlike = moderate, pangaea = low. The four-preset list stays stable. |
| 12 | **Caldera crater lakes by direct injection.** At mesh resolution a caldera is sub-grid, so `LakesStage` reads `ctx.volcanoes` and stamps a small terminal lake at each `has_caldera` cell rather than relying on erosion to carve one. The one deliberate cross-stage coupling. |

---

## 2. Output contract additions

`GridFields` / `MeshFields` gain three columns (auto-baked by `bake_to_grid`,
which gathers any `GridFields` name that exists on `MeshFields`):

- `volcanism` — present-day volcanic activity, `[0, 1]` f64.
- `is_volcano` — cell is a discrete volcano summit, bool.
- `volcano_id` — index into `WorldData.volcanoes`; `-1` = none, int32.

`WorldData` gains one list:

```python
volcanoes: list[Volcano]      # discrete volcanoes in mesh-cell coordinates
```

New feature object (`features.py`), parallel to `River`/`Lake`:

```python
class VolcanoKind(IntEnum):    # from mechanism
    STRATO = 0   # subduction arc
    SHIELD = 1   # hotspot
    FISSURE = 2  # rift / ridge

class VolcanoStatus(IntEnum):
    ACTIVE = 0
    DORMANT = 1
    EXTINCT = 2

@dataclass
class Volcano:
    id: int                 # 0-based; matches volcano_id columns
    cell: int               # mesh cell id of the summit
    kind: VolcanoKind
    status: VolcanoStatus
    has_caldera: bool        # forces a crater lake at `cell`
    chain_id: int            # arc/trail grouping; -1 = solitary
    activity: float          # [0,1] present-day intensity at the summit
```

Chains are an integer grouping (`chain_id`), not a separate object — same
lightweight pattern as `River.tributary_of`.

---

## 3. Geology model

### 3.1 Plate density & polarity (`plate_personalities.py`)

`PlateProperties` gains `density: Float64Array` (shape `(n_plates,)`):
continental plates get a low base density, oceanic a high one, plus a small
deterministic per-plate jitter so any two oceanic plates have a definite denser
one. At a convergent boundary the **denser plate subducts**; the other is the
**overriding** plate.

### 3.2 Shared boundary classifier (`terrain/boundaries.py`)

One walk over plate borders (the loop currently in
`boundary_uplift._compute_boundary_intensity`) produces, per cell, the dominant
cross-boundary relation:

```python
@dataclass(frozen=True)
class BoundaryFacts:
    convergence: Float64Array   # per-cell max convergent rate (>= 0)
    divergence: Float64Array    # per-cell max divergent rate (>= 0)
    kind: Int8Array             # dominant boundary kind (enum below)
    is_overriding: BoolArray    # cell sits on the overriding plate of a subduction
```

`BoundaryKind`: `NONE`, `CONV_OO`, `CONV_OC`, `CONV_CC`, `DIV_OO`, `DIV_OC`,
`DIV_CC` (O = oceanic, C = continental). Convergence/divergence magnitudes are
the same `dot(drift_i - drift_j, direction)` the current code computes.

Consumers:

- **`boundary_uplift.py`** (refactored): collision belts from `convergence`
  (all convergent kinds — mountains form regardless of volcanism), plus rift
  *valleys* only where the divergent boundary is **not** oceanic–oceanic
  (`DIV_OC`, `DIV_CC`). Oceanic–oceanic divergence is left for the vulcanism
  stage to *raise* into a ridge. Net terrain behavior is unchanged except that
  `DIV_OO` seams no longer carve down.
- **`VulcanismStage`** (new): everything in §3.3–3.5.

### 3.3 Subduction arcs

For cells with `kind in {CONV_OO, CONV_OC}` (never `CONV_CC`):

1. Seed arc potential at **overriding-side** boundary cells, weighted by
   `convergence`.
2. BFS-smear that potential *into the overriding plate* by `arc_offset` hops to
   place the arc inland of the trench, with a peak at `arc_offset` and a falloff
   over `arc_width` more hops (a multi-source BFS like `_smear_intensity`, but
   offset rather than centered on the seam).
3. Add `arc_uplift * potential` to `uplift`; add `potential` to the volcanism
   field.
4. `CONV_OC` overriding cells are continental → an **inland continental arc**;
   `CONV_OO` overriding cells are oceanic → an **offshore island arc** (the
   added uplift breaches sea level into a chain of islands).

### 3.4 Hotspots

`hotspot_count` points, placed by a greedy spacing scan biased to oceanic-plate
interior cells (far from boundary cells), with `hotspot_continental_fraction`
allowing the occasional continental hotspot. For each hotspot:

- Host plate `p = plate_id[cell]`; drift `d = drift[p]`.
- Stamp volcanoes at `pos_k = site(cell) + k * chain_step * d` (torus-wrapped)
  for `k = 0 .. chain_length`, snapping each to the nearest mesh cell.
- Edifice height `h_k = hotspot_peak_uplift * chain_decay**k`: `k=0` is the tall
  active shield; height decays down-trail so far cells subside into
  seamounts/atolls that finalize leaves below sea level.
- Each stamp adds a small radial uplift bump (a few cells, `volcano_radius`) and
  marks a `Volcano` (`SHIELD`, `chain_id = hotspot index`). Status: `ACTIVE` at
  `k=0`, `DORMANT` for the next few, `EXTINCT` beyond — by trail fraction.
- Volcanism field gets `chain_decay**k` activity (the head is hot, the tail dead
  → "present-day activity").

### 3.5 Rift / divergent volcanism

- `DIV_OO` (oceanic spreading): add `ridge_uplift * divergence` to `uplift` (a
  modest raised mid-ocean ridge replacing the old depression). Where ridge +
  noise breaches sea level, mark `FISSURE` volcanoes (Iceland). Volcanism field
  gets `divergence`.
- `DIV_OC` / `DIV_CC` (continental rift): boundary_uplift keeps the valley; the
  vulcanism stage adds flanking volcanism field and seeds occasional `FISSURE`
  volcanoes on the flanks.

### 3.6 Discrete volcano selection

Volcanoes are deterministic and spaced:

- **Hotspot:** every stamp cell (§3.4).
- **Arc:** local maxima of the arc volcanism band, accepted greedily with
  `volcano_spacing` (the nexus pattern) → a row of stratovolcanoes; `chain_id`
  per arc segment; status `ACTIVE`, a `dormant_fraction` rolled to `DORMANT`.
- **Rift:** spaced `FISSURE` volcanoes on high-volcanism rift/ridge cells.

A `caldera_fraction` of volcanoes is deterministically flagged `has_caldera`.

The volcanism field is the union of arc / hotspot / ridge / rift-flank
contributions, clipped to `[0, 1]`.

---

## 4. Pipeline & architecture

New order (changes in **bold**):

```
Plates → PlatePersonality(+density) → BoundaryUplift(refactored)
       → Vulcanism                                    ← NEW, before erosion
       → Erosion → Finalize
       → Insolation → Temperature → Wind → Moisture
       → Discharge → Rivers → Lakes(+caldera inject)   ← reads ctx.volcanoes
       → Flow
       → Savagery(+volcanism)                          ← new weight
       → Leylines(+volcano nexus bonus)                ← new score term
       → Biomes
```

- `WorldContext` gains `volcanoes: list[Volcano] | None` (set by
  `VulcanismStage`, finalized in place; consumed by Lakes/assembly).
- `VulcanismStage` writes `uplift` (in place), `volcanism`, `is_volcano`,
  `volcano_id`, and `ctx.volcanoes`.
- New `FIELD_*` ids in `rng.py` for the new noise fields (arc/ridge/hotspot
  jitter); new `ctx.seed_for("vulcanism*")` sub-seeds. No global RNG.
- `Volcano.activity` and final `status` are summit values read off the
  volcanism field after it's assembled.

### Caldera coupling (the one cross-stage thread)

`LakesStage` reads `ctx.volcanoes`; for each `has_caldera` volcano on land that
isn't already a lake cell, it sets `is_lake`/`lake_id` and appends a small
terminal `Lake` (the volcano's summit cell). Documented as the deliberate
exception to "each stage reads only its inputs".

---

## 5. Config (`VulcanismConfig`)

New dataclass on `WorldgenConfig` (`vulcanism`), grouped like the others:

```
# subduction
density_jitter            # per-plate density noise for OO polarity tiebreak
arc_uplift                # collision→edifice height multiplier
arc_offset                # BFS hops inland from trench to arc crest
arc_width                 # arc band falloff width (hops)
arc_volcano_spacing       # min spacing between arc stratovolcanoes (span frac)
dormant_fraction          # arc volcanoes rolled dormant
# hotspots
hotspot_count
hotspot_continental_fraction
chain_length              # stamps per hotspot
chain_step                # spacing along drift (span frac)
chain_decay               # height/activity multiplier per stamp
hotspot_peak_uplift       # active-head edifice height
# rifts / ridges
ridge_uplift              # oceanic-divergent ridge raise
rift_flank_strength       # continental-rift flank volcanism
# shared
volcano_radius            # radial uplift-bump radius (cells)
caldera_fraction          # volcanoes with a crater lake
# coupling (live in their own configs)
SavageryConfig.volcanism_weight
LeylineConfig.volcano_bonus
```

Presets (`presets.py`): archipelago high (hotspots + arcs build the islands),
wildlands high, earthlike moderate, pangaea low. Defaults on `WorldgenConfig()`
target earthlike-moderate.

---

## 6. Coupling detail

- **Savagery:** `compute_savagery` gains a `volcanism` arg and
  `cfg.volcanism_weight` term (volcanic ground is dangerous), normalized like
  the others, clipped to `[0,1]`.
- **Magic nexuses:** `place_nexuses` adds `cfg.volcano_bonus * fields.volcanism`
  to the score — volcanoes become prime nexus sites (it already biases toward
  peaks). No valence/channel change this round.
- **Biomes:** untouched. Volcanism is an overlay; the `argmax == BIOME_GRID`
  invariant holds. Volcanic-soil fertility is a future ecology-round field.

---

## 7. Validation

Viewer (`view_worldgen.py` / `export_worldgen.py`): new layers for the
volcanism field, volcano points, and (debug) the boundary-classifier `kind`.

Invariants (pytest, seed-parameterized):

- determinism — same seed → identical volcanoes and fields, twice.
- `volcanism ∈ [0,1]`; `is_volcano ⇔ volcano_id >= 0`; `volcano_id` indexes a
  real `Volcano`; `chain_id` groups are consistent.
- **zero volcanism at continent–continent convergent cells** (the signature
  subduction gate).
- arc volcanoes sit on the overriding plate (not the subducting one).
- hotspot trails: height/activity monotonically non-increasing down-trail; each
  oceanic hotspot yields ≥1 above-sea volcano.
- caldera volcanoes have a lake at their cell.
- bake parity: `grid.volcanism == mesh.volcanism[nearest]`.
- existing suites stay green (esp. the biome argmax invariant and land-fraction
  tolerance).

---

## 8. Phasing

| Phase | Deliverable |
|---|---|
| VP0 | `terrain/boundaries.py` shared classifier; refactor `boundary_uplift.py` to consume it; plate `density`. Existing tests green (DIV_OO no-carve is the only intended terrain delta). |
| VP1 | `VulcanismStage`: subduction arcs + hotspot trails + oceanic ridges into `uplift`; `volcanism`/`is_volcano`/`volcano_id` fields; `Volcano` object + `WorldData.volcanoes`; bake; viewer layers. |
| VP2 | Caldera crater lakes (`LakesStage` injection); finalize kind/status/chain/activity off the assembled field. |
| VP3 | Coupling — savagery `volcanism_weight`, nexus `volcano_bonus`; preset tuning. |
| VP4 | Full invariant suite, viewer/README/docs pass. |

Each phase ends runnable and visible in the viewer.

---

## 9. Seam left open (not built this round)

**Post-erosion crisp-cone pass.** Decision #3 keeps cones as eroded volcanic
mountains for causal integration. If the viewer shows them too mushy, a second
stage after `ErosionStage` can re-stamp sharp cones at the marked volcano cells
(the `ctx.volcanoes` list + `volcanism` field make this a clean, additive
change). Deferred until eyeballed — not committed blind.
