# Worldgen Architecture Redesign

Status: **design agreed; not yet implemented.** This document is the execution
contract for the redesign on branch `claude/worldgen-architecture-redesign-xzixr9`.
It supersedes the *organisational* guidance in `worldgen-redesign-plan.md` (which
remains the record of the algorithms that shipped); the algorithms themselves are
unchanged unless a phase below says otherwise.

---

## 0. Governing principles

These were chosen explicitly during the design interview and win every tie below.

1. **Long-term architecture beats beginner-friendliness and legacy preservation.**
   When a choice trades short-term simplicity for a cleaner long-term boundary, we
   take the boundary. We do *not* keep current shapes for their own sake.
2. **Dependency direction is sacred.** `src/core/model` is the foundation that
   everything depends *on*; it must never import *up* into `src/worldgen`. Getting
   this right now is the expensive-to-fix-later property, so it drives placement.
3. **One teachable rule for "where does a type live":** *does it outlive
   generation?* If a type is part of the persisted product, it is a **domain
   model** and lives in `core/model`. If it exists only while a world is being
   generated, it is **scratch** and stays in `worldgen`.
4. **Avoid speculative generality.** We add the layer that pays off now (clean
   dependency direction, a shared field contract) and defer layers that guard
   against futures that may never take their assumed shape (a producer↔domain
   anti-corruption layer with a single producer).

---

## 1. Scope & non-goals

**In scope:** `src/worldgen` and `src/core/model`. The `WorldData` output
*contract may change shape*.

**Out of scope this round:** `src/service/world.py`, `src/factory/world.py`, and
persistence. They already speak the *old* worldgen shape and are known-broken;
they are **not** fixed here. §8 records the new contract so their own round can
adopt it.

**Not a goal:** behaviour change. This is a structural redesign. Determinism
(same `seed`/`size` → identical output) is re-asserted every phase; any output
change is a bug unless a phase explicitly calls for one.

---

## 2. Decision log (interview)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Scope = `worldgen` + `core/model`; contract free to change; downstream deferred. | Room to reshape the data model without chasing persistence this round. |
| 2 | Placement rule: **ships in the product → `core/model`; generation-only scratch → `worldgen`.** Test: "does it outlive generation?" | One teachable, structural rule. |
| 3 | Feature objects **convert to tile/world coordinates at bake**; the Voronoi **mesh is fully ephemeral/internal**. | Product becomes self-contained — no dangling references into a discarded mesh. |
| 4 | Field presence: **eager, non-optional allocation.** Fields are plain arrays from creation; never `None`. | Deletes the per-stage `None`-narrowing ritual — the single biggest "spaghetti" source. |
| 5 | **One `Fields` type, two instances** (mesh-resolution scratch + grid-resolution product). Bake stays a generic gather. | Collapses the ~300 lines of duplicated `MeshFields`/`GridFields` to one declaration. |
| 6 | **Field schema (contract) lives in `core/model`** as a numpy-free registry; the typed `Fields` container + bake live in `worldgen`, derived from the schema; a **drift-guard test** keeps them aligned. | The data contract is a cross-system asset (worldgen + persistence + sim); it must not live inside one consumer. Core stays numpy-free. |
| 7 | **`WorldData` stays in `worldgen`** as the output envelope; reusable **entities + schema + enums move to `core/model`**. | `WorldData` embeds the worldgen `Fields` container and `WorldgenConfig`; putting it in core would invert the dependency. Most-robust *and* lowest-regret: it is the exact substrate for a core `World` aggregate later, if ever needed. |
| 8 | Core entities are **plain-Python, numpy-free, serialization-ready** (`list[float]`, tuples), tile/world coords as ints/tuples. | A dependency-light, persistence-friendly domain layer. Heavy per-tile bulk stays in the `Fields` container. |
| 9 | **Co-locate algorithm + `Stage` by domain; delete the flat `stages/` mirror.** | Everything about a concept in one place; keeps the pure/wiring split (testability) without the mirror-directory indirection. |
| 10 | Generation workspace = `config` + `geometry` + `fields` + a typed **scratch** namespace + a typed **outputs** collector. | Makes product-vs-plumbing legible in the type system, mirroring the core/model rule on the worldgen side. |
| 11 | `core/model` layout: **extend the existing `environment/<domain>/` taxonomy** (entities beside their bands; new `water/`, `magic/`, `regions/`); field schema in its own module, composed from per-domain field groups. | One organising principle, no competing parallel tree. |
| 12 | Type strictness: **concrete dtypes at the contract, broad aliases internally.** Schema-driven setter coerces dtype on write-back. | Captures types where they are a contract; tolerates numpy's widening in scratch. |
| 13 | **Stages declare their field reads/writes;** the pipeline keeps its hand-authored order but **validates dependencies at startup**. | Turns the eager-allocation "silent zeros on misorder" hole into a loud construction-time error; self-documents each stage's data contract. |
| 14 | Entity enums **harmonise to `StrEnum`** (incl. `NexusPolarity`); sign-semantics handled internally by the algorithm. | One enum convention across `core/model`; serializable products store labels, not opaque ints. |
| 15 | Execution: **incremental, determinism + invariants green and viewer working every phase**, carried through all phases to completion. | De-risks a deep change to a working system. |

---

## 3. Target architecture

### 3.1 Layering & dependency direction

```
src/core/model/                      (foundation — numpy-free, depended-upon only)
  environment/<domain>/              bands + entities + per-domain field groups
  environment/field_schema.py        FIELD_SCHEMA: the cross-system field contract
        ▲
        │ imports (never the reverse)
        │
src/worldgen/                        (producer — owns numpy machinery)
  fields.py                          typed Fields container, derived from schema
  workspace.py                       generation workspace (was context.py)
  pipeline.py                        ordered stages + dependency validation
  geometry/ noise/ config/           internal scratch + knobs
  terrain/ climate/ water/ magic/    domain packages: algorithm + Stage co-located
  ecology/ regions/
  bake/                              mesh→grid gather + feature coord translation
  world.py                           WorldData envelope (assembles core entities)
```

`core/model` **never** imports `worldgen`. `worldgen` imports `core/model` for the
schema, entities, and enums.

### 3.2 `core/model` layout

Extend the existing `environment/<domain>/` taxonomy. Each domain holds both its
classification bands (unchanged) and its new product entities + enums:

| Domain | Existing (bands) | New (entities + enums) |
|---|---|---|
| `terrain/` | `elevation.py` | `volcano.py` (`Volcano`, `VolcanoKind`, `VolcanoStatus`), `landmass.py` (`Landmass`) |
| `water/` *(new)* | — | `river.py` (`River`), `lake.py` (`Lake`) |
| `climate/` | `precipitation.py` | — |
| `ecology/` | `biome.py`, `savagery.py` | — |
| `magic/` *(new)* | — | `vein.py` (`Vein`), `nexus.py` (`Nexus`, `NexusPolarity`) |
| `regions/` *(new)* | — | `region.py` (`Region`, `RegionKind`) |
| `shared/` | temperature/wind | — |

Cross-cutting **field schema** lives at `environment/field_schema.py`, composed
from per-domain field-group lists (`terrain/fields.py`, `climate/fields.py`, …)
so a domain's fields are declared next to its other domain types and the global
`FIELD_SCHEMA` is their ordered concatenation.

All entities are **plain-Python and numpy-free** (Decision 8):

- `River.discharge: tuple[float, ...]` (per-step along the path), `cells:
  list[tuple[int, int]]` (tile coords), `mouth: tuple[int, int]`, `tributary_of:
  int | None`.
- `Lake.cells: list[tuple[int, int]]`, `surface_level: float`, `outlet:
  tuple[int, int] | None`.
- `Volcano.cell: tuple[int, int]`, `kind: VolcanoKind`, `status: VolcanoStatus`,
  `activity: float`, …
- `Nexus.cell`, `polarity: NexusPolarity`, `charge: float`, `channels:
  tuple[float, float, float]`.
- `Vein.cells`, `strength: tuple[float, ...]`, `channels: list[tuple[float,
  float, float]]`, nexus refs.
- `Region.centroid: tuple[float, float]`, `kind: RegionKind`, `name: str`, …

All entity enums are `StrEnum` (Decision 14). Where the algorithm needs a signed
number (e.g. nexus polarity multiplying into the ley potential), it maps the
`StrEnum` to ±1 *internally*; the shipped entity carries the label.

### 3.3 Field schema — the contract

`FIELD_SCHEMA: tuple[FieldSpec, ...]`, a pure-stdlib ordered registry. `FieldSpec`
is a frozen dataclass:

```python
@dataclass(frozen=True)
class FieldSpec:
    name: str
    dtype: str            # token: "f8" | "i4" | "i1" | "bool"   (numpy-free)
    shape: FieldShape     # SCALAR | CHANNELS(3) | BIOMES(n)     (2nd-axis size)
    lo: float | None      # documented range, contract-checked in tests
    hi: float | None
    doc: str
    ships_to_product: bool
```

- `dtype` is a **string token** so `core/model` takes no numpy dependency;
  `worldgen` maps tokens → `np.dtype`.
- `shape` covers the 2-D fields (`magic_channels` → `CHANNELS(3)`,
  `biome_weights` → `BIOMES(n)` where `n` is the `BiomeEnum` cardinality).
- `ships_to_product` drives the bake (3.5): intermediates like `insolation`,
  `uplift`, `z_route`, `receiver`, `plate_id` are `False` and never cross to the
  grid product.

The schema is the single source of truth for **persistence** (column schema),
**sim/gameplay** (field metadata), and **worldgen** (allocation/bake). It also,
finally, *captures* the per-field dtype + range + meaning in one place — the
"types aren't fully captured" complaint resolved at the schema level.

### 3.4 `Fields` container (worldgen)

One typed dataclass, **declared once**, used for both the mesh-resolution scratch
instance and the grid-resolution product instance (Decision 5).

- **Eager, non-optional allocation** (Decision 4): `Fields.allocate(n)` zero-fills
  every array at the schema's dtype/shape. Attributes are concrete arrays
  (`elevation: Float64Array`), never `None`. The per-stage `None`-narrowing ritual
  is **deleted everywhere**.
- **Static typing preserved**: the dataclass is hand-written (autocomplete works);
  `allocate`/bake are driven by `FIELD_SCHEMA`. A **drift-guard test** asserts the
  dataclass field names == schema names, in order — they cannot silently diverge.
  Contributor rule: add a field in the domain schema group **and** the `Fields`
  dataclass; the test enforces both.
- **Dtype coercion on write-back** (Decision 12): a schema-aware setter coerces an
  assigned array to the field's concrete dtype, so algorithm internals may compute
  in numpy's widened types (broad aliases) and the storage slot stays exact.

### 3.5 Bake (mesh → grid)

The bake stays a **generic nearest-cell gather** (`value[nearest]` over axis 0,
2-D fields ride the same path), now driven by the schema:

1. Gather **only `ships_to_product` fields** onto the grid `Fields` instance.
   Non-shipping intermediates remain at their zero allocation on the grid (present
   as attributes, unpopulated) — one type, curated product *content*.
2. **Translate feature geometry to tile/world coordinates** (Decision 3). The bake
   owns the mesh-cell-id → tile-coord mapping and rewrites each entity's geometry
   (`River.cells`, `Lake.cells`, `Volcano.cell`, `Vein.cells`, `Nexus.cell`) into
   the product coordinate space. After bake, **no shipped object references a
   mesh-cell id.** Note mesh→tile is many→one, so some path detail collapses; the
   per-tile `*_id` columns remain the dense per-tile lookup.

### 3.6 Worldgen module layout

Co-locate each concept's algorithm and its thin `Stage` in its domain package;
**delete the flat `stages/` directory** (Decision 9):

```
worldgen/terrain/erosion.py     →  erode(...)        (pure, keyword-only, tested)
                                   ErosionStage      (thin wiring: reads cfg+fields,
                                                      calls erode, writes fields)
worldgen/climate/temperature.py →  compute_temperature(...) + TemperatureStage
...
```

Pure modules shared by several stages (e.g. `terrain/boundaries.py`) stay
algorithm-only. The pure/wiring split (the basis of unit-testability) is preserved
*within* the domain package; the cross-tree mirror is gone.

### 3.7 Generation workspace (was `WorldContext`)

A `Workspace` dataclass — the shared mutable generation buffer — with the
scratch/outputs split (Decision 10):

```python
@dataclass
class Workspace:
    config: WorldgenConfig
    geometry: MeshGeometry
    fields: Fields                  # eager bulk arrays (mesh-resolution)
    scratch: Scratch                # internal artifacts, never shipped
    outputs: Outputs                # product entity collections, harvested to WorldData
    # seed_for / noise_for helpers unchanged
```

- `Scratch` holds `plate_properties`, `boundary_facts`, `volcano_candidates`,
  `magic_potential`, … — generation-only (these stay typed; the viewer reaches
  them through `run_debug`, so the whole workspace is the debug surface and the
  old `magic_potential` "for the viewer/tests" leak is now structurally where it
  belongs).
- `Outputs` accumulates `rivers`, `lakes`, `volcanoes`, `veins`, `nexuses`,
  `regions`. `world.py` harvests `outputs` (post-bake, in tile coords) into
  `WorldData`.

### 3.8 Stage protocol + dependency validation

```python
class Stage(Protocol):
    reads: tuple[str, ...]          # field names consumed
    writes: tuple[str, ...]         # field names produced
    def run(self, ws: Workspace) -> None: ...
```

The pipeline keeps its **explicit, hand-authored order** (physical rationale like
wind-before-temperature is preserved). At construction it **validates**: every
name in a stage's `reads` must appear in some earlier stage's `writes` (or be a
base-allocated input). Misordering is now a **loud startup error**, not silent
zeros (Decision 13). An optional debug "written" guard can assert reads/writes at
runtime.

### 3.9 `WorldData` envelope

Stays in `worldgen/world.py` (Decision 7): the output envelope aggregating the
grid `Fields` product, `WorldgenConfig` (reproducibility), and the core-model
entity lists. `WorldgenConfig` and its sub-configs stay in `worldgen/config/`
(generation knobs, not domain models), regrouped to match the domain packages.

---

## 4. Types & enums summary

- `worldgen/types.py`: concrete contract aliases (`Float64Array =
  NDArray[np.float64]`, `Int32Array = NDArray[np.int32]`, `Int8Array`,
  `BoolArray`) for storage; broad aliases (`FloatArray = NDArray[np.floating]`,
  `IntArray`) for algorithm internals. No more "widened from …" apologetic
  aliases.
- Scratch enums that index arrays and live only in worldgen (e.g. `BoundaryKind`
  as `int8` codes) stay `IntEnum`.
- All **shipped entity** enums are `StrEnum`.

---

## 5. Execution phases

Incremental; each phase ends **runnable, viewer working, determinism +
invariants green** (Decision 15). Carry through all phases to completion.

| Phase | Deliverable | Done when |
|---|---|---|
| **1 — Field contract & container** | `FIELD_SCHEMA` (+ per-domain groups) in `core/model`; unified `Fields` container in worldgen with eager non-optional allocation + dtype-coercing setter; drift-guard test. Replace `MeshFields`/`GridFields` with the two-instance model. | Pipeline runs on the new `Fields`; `None`-narrowing ritual gone from stages; determinism identical. |
| **2 — Entity relocation** | Move `River/Lake/Volcano/Vein/Nexus/Region/Landmass` + enums into `core/model/environment/<domain>/`; make them numpy-free plain-Python; harmonise enums to `StrEnum`. | `core/model` imports clean (no numpy, no upward import); `WorldData` assembles from core entities. |
| **3 — Module co-location** | Co-locate each algorithm + `Stage` in its domain package; delete `worldgen/stages/`; update `pipeline.py` imports. Naming cleanup (`plate`→`plates`, etc.). | One place per concept; suite green. |
| **4 — Workspace & stage deps** | Introduce `Workspace` (scratch/outputs split); add `reads`/`writes` to every stage; pipeline dependency validation at startup. | Deliberate misorder raises at construction; viewer reads scratch via `run_debug`. |
| **5 — Type tightening** | Concrete contract aliases; broad internal aliases; coercion at write-back; remove apologetic alias comments. | `ruff` clean; pyright basic clean. |
| **6 — Bake coords & contract notes** | Bake translates feature geometry to tile/world coords (no shipped mesh-id refs); `ships_to_product` curation; document the new `WorldData` contract for the deferred downstream round. | No shipped object references a mesh-cell id; product self-contained. |

---

## 6. Validation strategy

Retain the existing instruments and extend them:

- **Determinism** re-asserted every phase (same seed/size → identical arrays +
  entities), parameterised over 2–3 seeds.
- **Invariant suite** (terrain/water/climate/ecology) unchanged in intent; ranges
  now checked against `FieldSpec.lo/hi`.
- **New: drift-guard test** (`Fields` dataclass ↔ `FIELD_SCHEMA` agree).
- **New: dependency-validation test** (a deliberately misordered pipeline raises).
- **New: coordinate test** (no shipped entity references a mesh-cell id; tile
  coords in `[0,size)`).
- **Viewer first**: `scripts/view_worldgen.py` / `worldgen_render.py` keep working
  every phase, reading the grid `Fields` (baked) and scratch via `run_debug`.
- **Smoke renders**: fixed-seed PNGs for eyeballing; not compared automatically.

---

## 7. Risks & mitigations

- **Eager allocation memory** (≈40 arrays × `n` + 2-D `biome_weights` (n, ~48)):
  acceptable at the existing `cell_count_cap`; the arrays are allocated eventually
  anyway. Mitigation: allocation is the same total, just earlier.
- **Eager allocation hides misorder** → closed structurally by stage
  `reads`/`writes` validation (3.8).
- **Schema/container drift** → closed by the drift-guard test (3.4).
- **Coordinate-translation detail loss** (mesh→tile many→one) → accepted;
  per-tile `*_id` columns remain the dense lookup; path objects are summaries.

---

## 8. Out of scope — downstream contract note

`src/service/world.py` and `src/factory/world.py` consume the **old** worldgen
shape and stay known-broken this round. Their adoption round inherits this
contract:

- The persisted product is `WorldData` = `Fields` grid product (shipping fields
  only) + `WorldgenConfig` + numpy-free core entity lists in **tile/world
  coordinates**.
- The field column schema is `FIELD_SCHEMA` (`ships_to_product == True`),
  authoritative for persistence DDL and gameplay field access.
- Entities are serialization-ready (`StrEnum` kinds, plain-Python payloads).
- `region_id` remains the per-tile socket for the future geography-clustering
  tier.
