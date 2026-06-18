# Phase 3 — Water: Discharge, Rivers, Lakes

*Prerequisite: Phase 2. Medium-sized phase. The flow tree from Phase 1 does
most of the work; this phase reads the answers off it and turns them into
game objects.*

**What Phase 3 delivers:** rivers as first-class objects (paths with identity,
tributaries, mouths), lakes with real outlets, per-cell flow direction and
speed, and the rasterization that stamps it all onto the tile grid.

**Concepts you'll learn:** trees as arrays (the receiver array *is* a tree),
walking and merging paths, connected components (again — they're everywhere),
and line rasterization.

New fields: `discharge`, `is_river`, `river_id`, `flow_u`, `flow_v`,
`flow_speed`, `is_lake`, `lake_id`. New module: `water/`. New dataclasses
(in `worldgen/features.py` — these ship inside `WorldData`):

```python
@dataclass
class River:
    id: int
    cells: list[int]          # source → mouth, mesh cell ids
    discharge: np.ndarray     # per step
    mouth: int                # cell id (ocean or lake cell)
    tributary_of: int | None  # river id it joins, None for trunk rivers

@dataclass
class Lake:
    id: int
    cells: list[int]
    surface_level: float      # from z_route
    outlet_cell: int | None   # spill cell; None = terminal (endorheic) lake
```

---

## Before you start (house style — read `CONVENTIONS.md`)

> **All code in this phase must match `docs/worldgen-guide/CONVENTIONS.md`.**
> Pure functions in a new `src/worldgen/water/` package; thin `Stage` wrappers in
> `stages/`. This phase also introduces **feature objects** (`River`, `Lake`) and
> a **river rasterizer** — both have a designated home below.

**Files you will create:**

```
src/worldgen/features.py           # @dataclass River, Lake (and Landmass if not already)
src/worldgen/water/
    discharge.py                   # pure: accumulate_discharge(...)
    rivers.py                      # pure: classify_rivers(...), extract_rivers(...)
    lakes.py                       # pure: extract_lakes(...)
    flow.py                        # pure: compute_flow(...)
src/worldgen/stages/
    discharge.py                   # DischargeStage
    rivers.py                      # RiversStage
    lakes.py                       # LakesStage
    flow.py                        # FlowStage
src/worldgen/bake/rivers.py        # stamp_rivers(...) — see step 6
```

> The `River`/`Lake` dataclasses follow the same `@dataclass` style as
> `PlateProperties` (`terrain/plate_personalities.py`): plain dataclass, typed
> fields, `np.ndarray` where appropriate. They are **not** mesh fields; they live
> on the eventual `WorldData` (Phase 5) and are carried on the context meanwhile
> (e.g. `ctx.rivers`, `ctx.lakes` — add these `list[...] | None` slots to
> `WorldContext` the same way `plate_properties` was added).

**Fields to add** (both `MeshFields` and `GridFields`, `dtype` metadata + `#`):

```python
discharge: Float64Array | None = field(default=None, metadata={"dtype": np.float64})   # Rain-weighted water flow
is_river: BoolArray | None = field(default=None, metadata={"dtype": bool})              # Cell carries a river
river_id: Int32Array | None = field(default=None, metadata={"dtype": np.int32})         # River object id; -1 = none
flow_u: Float64Array | None = field(default=None, metadata={"dtype": np.float64})       # unit flow direction x
flow_v: Float64Array | None = field(default=None, metadata={"dtype": np.float64})       # unit flow direction y
flow_speed: Float64Array | None = field(default=None, metadata={"dtype": np.float64})   # [0,1] stylized speed
is_lake: BoolArray | None = field(default=None, metadata={"dtype": bool})               # Cell is under lake water
lake_id: Int32Array | None = field(default=None, metadata={"dtype": np.int32})          # Lake object id; -1 = none
```

> `river_id`/`lake_id` should default to `-1`, not `0`, so "no feature" is
> distinct from "feature #0". The generic `allocate` zeroes arrays — so **set them
> to `-1` explicitly** in the stage that writes them (e.g.
> `ctx.fields.river_id = np.full(n, -1, dtype=np.int32)` before stamping).

**Config to add:** `RiverConfig` (`river_fraction`, rasterizer `w_scale`,
`min_w`, `max_w`), `LakeConfig` (`epsilon`). Register on `WorldgenConfig`.

**The reusable BFS:** this phase needs connected components a fourth time. Factor
`components(geometry, mask) -> Int32Array` into `water/lakes.py` (or a small
`geometry/graph.py`) and reuse it; mirror the BFS shape in
`terrain/finalize.py::label_landmasses` exactly (queue = `deque`, visited mask,
`int(neighbor_id)` conversion).

**Pipeline** — append in order: `DischargeStage(), RiversStage(), LakesStage(),
FlowStage()`. The grid bake + `stamp_rivers` run after the pipeline (viewer/Phase
5 territory).

---

## Step 1 — Discharge: rain-weighted accumulation (1 h)

### The lesson first

Phase 1's `drainage` answered "how many cells drain through here?" — uniform
rain, the right driver for erosion. The game wants "how much *water* flows
here?" — and you now have an actual rain map. Same accumulation loop, one
change: cells contribute `precipitation[i]` instead of `1.0`.

This is the planning decision paying off: a river draining a rainforest now
dwarfs one draining a desert, even at equal basin size. Deserts can still
carry one big river fed by far-off wet mountains — if your map grows a Nile,
the system is working.

### What to build

Re-run the routing trio once on *final* terrain (priority-flood → receivers →
accumulate-with-precipitation), writing `discharge`. Ocean cells: zero it —
discharge is a land concept.

**Check (viewer):** `discharge` layer (log scale, like drainage). Compare
against `drainage`: same tree shapes, different weights — branches in wet
regions should glow brighter.

### Implementation scaffold (house style)

Reuse Phase 1's routing trio on **final** terrain. `water/discharge.py`:

```python
def accumulate_discharge(
    *,
    receiver: Int32Array,
    z_route: Float64Array,
    precipitation: Float64Array,
    is_land: BoolArray,
) -> Float64Array:
    """Like Phase 1 drainage, but each cell contributes precipitation[i]; ocean zeroed."""
```

`DischargeStage.run`: re-run `priority_flood → compute_receivers` on
`ctx.fields.elevation` (final terrain), then call `accumulate_discharge(...)`.
Store the fresh `z_route`/`receiver` back on `ctx.fields` — steps 3–5 depend on
them matching the final terrain, not the last erosion iteration's.

**Definition of done:** `discharge` is the drainage loop with one line changed
(`drainage[:] = precipitation` instead of `1.0`); ocean cells zeroed.

**Pitfalls:** do **not** reuse Phase 1's `drainage` array — it was uniform-rain
for erosion. Recompute the flow tree on final elevation so river cells line up
with the carved valleys.

---

## Step 2 — Which cells are rivers (30 min)

`is_river = is_land & ~is_lake_water & (discharge >= threshold)`.

For the threshold, prefer a *percentile* (`np.quantile(discharge[land], cfg.river_fraction)`)
over an absolute number — it self-adjusts across world sizes and wetness
levels, one less knob to retune per preset. (`is_lake_water` arrives in
step 4; use `z < z_route` meanwhile — same thing.)

**Check (viewer):** overlay river cells on elevation. Branching networks
hugging your valleys — they *will* hug them, because erosion carved the
valleys along the same flow tree. That agreement was the point of Phase 1.

### Implementation scaffold (house style)

`water/rivers.py`:

```python
def classify_rivers(
    *,
    discharge: Float64Array,
    is_land: BoolArray,
    is_lake: BoolArray,
    cfg: RiverConfig,
) -> BoolArray:
    """is_river = land & not-lake-water & discharge >= percentile threshold."""
```

`RiverConfig.river_fraction` is the **percentile** (e.g. `0.05` → top 5% of land
discharge are rivers), passed to
`np.quantile(a=discharge[is_land], q=1.0 - cfg.river_fraction)`.

**Definition of done:** threshold is a percentile of *land* discharge (self-
adjusting), not an absolute number; `is_lake` may not exist yet — use
`z < z_route` as the stand-in (same thing) and rewire to `is_lake` after step 4.

---

## Step 3 — Rivers as objects (3–4 h)

### The lesson first

The receiver array is secretly a forest (each cell points at one parent —
that's the definition of a forest), and rivers are just labeled paths in it.
The only design question is what happens at a **junction** where two rivers
meet: which one keeps its identity downstream? Convention (and real
cartography): **the larger discharge keeps the name**; the smaller one ends
there and is recorded as a tributary.

The clean construction inverts the walk — build *downstream-first*:

1. **Sources**: river cells with no river cell flowing *into* them (compute
   in-river-degree: for each river cell, count river cells whose receiver it
   is; sources have zero).
2. Process river cells in descending `z_route` order (same topological trick
   as accumulation — by now it should feel like an old friend). Each river
   cell asks: of the river cells flowing into me, whose discharge is largest?
   I continue *that* river; everyone else's river ends here,
   `tributary_of = my river`. A river cell with no river inflow starts a new
   `River`.
3. A river ends (records its `mouth`) when its receiver is ocean, a lake cell,
   or not a river cell.

Write `river_id` per cell as you go (cells below threshold keep `-1`).

### What to build

```python
def extract_rivers(geometry, fields) -> list[River]
```

**Check (REPL):** for several seeds — every river's `cells` are contiguous
(`receiver[cells[k]] == cells[k+1]`); discharge is non-decreasing along each
river (water only accumulates downstream — *the* invariant for this step;
make it a pytest); `tributary_of` never points at a river with smaller
maximum discharge.

### Implementation scaffold (house style)

`water/rivers.py`:

```python
def extract_rivers(
    *,
    geometry: MeshGeometry,
    receiver: Int32Array,
    discharge: Float64Array,
    z_route: Float64Array,
    is_river: BoolArray,
    is_lake: BoolArray,
) -> tuple[list[River], Int32Array]:
    """Build downstream-first River objects; return (rivers, river_id per cell, -1 = none)."""
```

`River` (in `features.py`): `id: int`, `cells: list[int]`,
`discharge: Float64Array`, `mouth: int`, `tributary_of: int | None`.

Algorithm order (per prose): compute in-river-degree, process river cells in
**descending `z_route`** (the Phase 1 topological trick), larger-discharge inflow
keeps the river identity, others record `tributary_of`. Write `river_id` as you
go; non-river cells stay `-1`.

**Definition of done:** the discharge-monotone invariant is a pytest, not just a
REPL check (Phase 5 `test_water.py` needs it).

**Pitfalls:** "in-river-degree" counts only **river** cells flowing in (a cell
whose `receiver` is this cell **and** `is_river`); a river ends when its receiver
is ocean, a lake cell, or non-river. Break discharge ties at junctions by cell id
so the result is deterministic.

---

## Step 4 — Lakes with outlets (2–3 h)

### The lesson first

Phase 1's priority-flood already found every lake — it just didn't write them
down. A lake is a connected blob of cells where `z < z_route` (terrain below
the water surface), its surface is their shared `z_route` value, and its
outlet is the spill cell the flood passed through. The old code's `LakeBasin`
died waiting for exactly this data.

### What to build

1. `lake_mask = is_land & (z_route > z + epsilon)`.
2. Connected components over the mask (BFS — fourth time, write it once as a
   `components(geometry, mask)` utility if you haven't already) → `lake_id`,
   `Lake.cells`, `surface_level = z_route` of any member.
3. **Outlet**: the boundary cell of the lake whose neighbor outside the lake
   has the lowest `z_route` — that's where the flood spilled in, and
   therefore where water spills out. If every outside neighbor is higher
   (rare, but possible with `base_level_fraction` quirks), the lake is
   terminal: `outlet_cell = None`.
4. Stitch rivers through: a river whose mouth is a lake cell ends there; the
   lake's outlet cell (if it's a river cell — it usually is, the lake's whole
   catchment drains through it) is the *source* of a new river. Record the
   relationship: continuing river's `tributary_of = None`, but add
   `Lake.outlet_river_id` if you find you want it. Don't over-model — stop at
   what the rasterizer and tests need.

**Check (viewer):** `lakes` layer over elevation. Lakes should sit in
mountain-bowl and rift locations, each with a river leaving from one edge.
Test: every non-terminal lake's outlet chain reaches the ocean (follow
receiver from outlet; bounded steps).

### Implementation scaffold (house style)

`water/lakes.py`:

```python
def extract_lakes(
    *,
    geometry: MeshGeometry,
    z: Float64Array,
    z_route: Float64Array,
    is_land: BoolArray,
    cfg: LakeConfig,
) -> tuple[list[Lake], Int32Array, BoolArray]:
    """Connected components of (is_land & z_route > z + eps); return (lakes, lake_id, is_lake)."""
```

`Lake` (in `features.py`): `id: int`, `cells: list[int]`,
`surface_level: float`, `outlet_cell: int | None`.

**Definition of done:** uses the shared `components(geometry, mask)` helper;
`surface_level` = `z_route` of any member; outlet = boundary cell whose **outside**
neighbor has the lowest `z_route`; all-higher → `outlet_cell = None` (terminal).
`is_lake` written; `lake_id` defaults `-1`.

**Pitfalls:** the lake mask is `is_land & (z_route > z + cfg.epsilon)` — the
epsilon avoids labeling numerically-flat-but-not-bowl cells. Stitch rivers
through lakes (step 4.4) only as far as the rasterizer/tests need; do not
over-model.

---

## Step 5 — Direction and speed (1–2 h)

Per river/land cell:

- **Direction**: unit `torus_delta(site[i] → site[receiver[i]])` →
  `flow_u/flow_v`. (Zero for non-river cells if you prefer clean data; the
  bake copies whatever you decide.)
- **Speed**: the Manning-flavored stylization from planning:
  `flow_speed = normalize(slope_along_flow^0.3 * discharge^0.2)`, where
  `slope_along_flow = (z[i] - z[receiver]) / dist`, floored at a tiny epsilon
  inside lakes so lake-crossing reaches come out near-still. Normalize to
  [0, 1] by percentile like precipitation.

**Check (viewer):** speed layer — bright fast headwaters in the mountains,
broad dim lowland trunks. If it's inverted, an exponent sign is wrong.

### Implementation scaffold (house style)

`water/flow.py`:

```python
def compute_flow(
    *,
    geometry: MeshGeometry,
    receiver: Int32Array,
    elevation: Float64Array,
    discharge: Float64Array,
    is_lake: BoolArray,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Return (flow_u, flow_v, flow_speed): unit direction to receiver + stylized Manning speed."""
```

**Definition of done:** direction = unit `torus_delta(site[i] → site[receiver])`;
`flow_speed = normalize(slope_along_flow**0.3 * discharge**0.2)` with
`slope_along_flow = (z[i] - z[receiver]) / dist`, floored at a tiny epsilon inside
lakes; normalize by percentile (like precipitation). Non-river cells may be zeroed.

**Pitfalls:** `receiver == -1` cells have no direction — leave them zero; use
`torus_distance` for `dist`; keep the `0.3`/`0.2` exponents in config-free form
only because they are part of the stylized formula (document them).

---

## Step 6 — Rasterize to the grid (2–3 h)

### The lesson first

Rivers are mesh-space polylines; tiles are pixels. Stamping a line onto a grid
is rasterization, and the simple robust method is the one the old code already
used: walk the segment in small steps, stamp a disk at each step. We keep that
but feed it river *paths* (so tiles learn `river_id`) and discharge-scaled
width: `radius = clip(w_scale * sqrt(discharge), min_w, max_w)` — `sqrt`
because river width grows sub-linearly with flow (a river 4× the flow looks
~2× as wide).

Mind the wrap: segment endpoints via minimum-image (`torus_delta`), stamped
tile coordinates via `% size`.

### What to build

`bake/rivers.py`: after the generic field bake, for each `River`, for each
consecutive cell pair, stamp: `is_river=True`, `river_id` (largest discharge
wins on contested tiles), `discharge`/`flow_*`/`flow_speed` from the wetter
stamp. Lakes: tiles inherit `is_lake`/`lake_id` through the generic bake
already — no special pass needed.

**Check (viewer):** switch the viewer's river layer from mesh cells to grid
tiles. Continuous rivers (no gaps where mesh cells were sparse), tapering
widths, lakes intact.

### Implementation scaffold (house style)

`bake/rivers.py` — runs **after** the generic `bake_to_grid` (it overwrites
river tiles), not as a `Stage`:

```python
def stamp_rivers(
    *,
    grid: GridFields,
    rivers: list[River],
    geometry: MeshGeometry,
    size: int,
    cfg: RiverConfig,
) -> None:
    """Walk each river's site-to-site segments, stamping disks onto grid tiles in place."""
```

**Definition of done:** segment endpoints via `torus_delta` (minimum-image),
stamped tile coords via `% size`; `radius = clip(w_scale * sqrt(discharge),
min_w, max_w)`; on contested tiles the **larger discharge** wins `river_id` and
`flow_*`. Lakes need no special pass — they bake through the generic path.

**Pitfalls:** `sqrt(discharge)` (sub-linear width), not linear; a segment that
crosses the seam draws as two partial segments (or stamp in torus space then
`% size`); do not forget to seed `is_river`/`river_id` tiles to `False`/`-1`
before stamping.

### Test scaffold (house style)

`test/worldgen/test_water.py` (Phase 5 keeps this name), fast fixture,
parameterized by seed:

```python
@pytest.mark.parametrize("seed", [1, 7, 42])
def test_discharge_monotone_along_rivers(seed: int) -> None:
    """Water only accumulates downstream."""

@pytest.mark.parametrize("seed", [1, 7, 42])
def test_lake_outlets_reach_ocean(seed: int) -> None:
    """Following receiver from each non-terminal outlet hits base level in bounded steps."""
```

## Exit criteria

- [ ] `River`/`Lake` objects in `WorldData`; `LakeBasin` memory honored
- [ ] Rivers flow through lakes and out their spillways to the ocean
- [ ] Per-tile: `is_river`, `river_id`, `discharge`, `flow_u/v`, `flow_speed`,
      `is_lake`, `lake_id`
- [ ] Invariants green: discharge monotone along rivers, all rivers terminate,
      lake outlets reach ocean, determinism

**Phase 4** is the fantasy layer: terrain-bred savagery, the leyline web, and
biomes — the last fields the world needs.
