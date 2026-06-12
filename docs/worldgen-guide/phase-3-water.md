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

## Exit criteria

- [ ] `River`/`Lake` objects in `WorldData`; `LakeBasin` memory honored
- [ ] Rivers flow through lakes and out their spillways to the ocean
- [ ] Per-tile: `is_river`, `river_id`, `discharge`, `flow_u/v`, `flow_speed`,
      `is_lake`, `lake_id`
- [ ] Invariants green: discharge monotone along rivers, all rivers terminate,
      lake outlets reach ocean, determinism

**Phase 4** is the fantasy layer: terrain-bred savagery, the leyline web, and
biomes — the last fields the world needs.
