# Worldgen Rebuild — Phase 0: Foundations

*A guided exercise. You write the code; this document tells you what to build,
why it's built that way, and how to prove to yourself it works. Read each step
fully before typing anything. The micro-steps are ordered so the project runs
after every single one.*

**What Phase 0 delivers:** the skeleton everything else plugs into — typed
array-based field storage, the torus Voronoi mesh producing that storage,
deterministic seeded noise with no global state, a pipeline shell with one
placeholder elevation stage, a viewer that can show it, and the first two
invariant tests. No real algorithms yet (plates and erosion are Phase 1) —
Phase 0 is about getting the *shape* of the system right.

**Concepts you'll learn:** struct-of-arrays vs array-of-structs, numpy
vectorization, CSR adjacency (how graph libraries actually store graphs),
why global RNG state is a bug factory, deterministic sub-seeding, and
KD-trees for nearest-neighbor lookup.

Keep the old code around while you work — we build the new package alongside
it and delete the old one at the end of the phase.

---

## Step 0 — Housekeeping (15 min)

1. Add `numpy>=2.0` to `pyproject.toml` dependencies (we've been using it
   secretly through scipy; make it honest) and run `uv sync`.
2. Create the new skeleton *next to* the existing modules:

   ```
   src/worldgen/
       fields.py        # new — step 1
       geometry/
           mesh.py      # new — steps 2–3
       noise/
           rng.py       # new — step 4
       bake.py          # new — step 6
   ```

3. Don't touch `data.py`, `stages/`, or the old `noise/sampler.py` yet.

**Check:** `uv run python -c "import numpy; print(numpy.__version__)"`.

---

## Step 1 — `MeshFields`: the struct-of-arrays (1–2 h)

### The lesson first

The old code stores the world as 12,000 `MeshCell` objects, each with 17
attributes. That layout is called **array-of-structs (AoS)**: one Python object
per cell. It has two costs:

- *Speed*: `for cell in cells: cell.temperature = ...` runs the Python
  interpreter 12,000 times. The numpy equivalent runs compiled C once.
- *Duplication*: every field exists twice (mesh cell + grid tile) and is copied
  by hand, field by field. You've seen where that leads.

The replacement is **struct-of-arrays (SoA)**: *one object total*, holding one
array per field. Cell #371's temperature is `fields.temperature[371]`. A whole
stage becomes an array expression:

```python
# AoS — 12,000 interpreter round-trips:
for cell in cells:
    cell.temperature = max(0.0, base[cell.id] - cell.z * lapse)

# SoA — one:
fields.temperature = np.maximum(0.0, base - fields.z * lapse)
```

### What to build

In `fields.py`, a dataclass where every field is a numpy array indexed by cell
id. Start with only what Phase 0 needs — fields get *added* in later phases,
which is now a one-line change:

```python
@dataclass
class MeshFields:
    elevation: np.ndarray   # float64, shape (n,)
    is_land: np.ndarray     # bool,    shape (n,)

    @classmethod
    def allocate(cls, n: int) -> MeshFields: ...
```

`allocate` creates zeroed arrays (`np.zeros(n)`, `np.zeros(n, dtype=bool)`).
Write it generically if you can — iterate `dataclasses.fields(cls)` and read
each field's dtype from metadata, e.g.
`field(metadata={"dtype": np.float64})` — because the generic version is what
makes "add a field = one line" true. If the generic version fights you, write
it explicitly and refactor later; both are acceptable Phase 0 exits.

**Check (REPL):** `MeshFields.allocate(10).elevation.shape == (10,)`, dtype
checks, and confirm two `allocate(10)` calls don't share arrays
(`a.elevation is not b.elevation`).

---

## Step 2 — `MeshGeometry`: CSR adjacency (1–2 h)

### The lesson first

Fields change every stage; *geometry* (where cells are, who neighbors whom)
is built once and never mutated. Separating them keeps mutation honest.

Positions are easy: `sites`, a `(n, 2)` float array. Neighbors are the
interesting part. Each cell has a *different number* of neighbors (5–8ish), so
a rectangular array doesn't fit, and a `list[list[int]]` reintroduces
slow Python objects. The standard answer — used by scipy.sparse, by every
graph library — is **CSR (compressed sparse row)**: two flat arrays.

- `neighbor_indices`: all neighbor lists concatenated into one int array.
- `neighbor_offsets`: where each cell's slice starts; length `n + 1`.

Cell `i`'s neighbors are
`neighbor_indices[neighbor_offsets[i] : neighbor_offsets[i+1]]`.

Tiny example — 3 cells, where 0↔1, 1↔2:

```
neighbors of 0: [1]      neighbor_offsets = [0, 1, 3, 4]
neighbors of 1: [0, 2]   neighbor_indices = [1, 0, 2, 0+... 
neighbors of 2: [1]                        = [1, 0, 2, 1]
```

Read it back: cell 1's slice is `indices[1:3] == [0, 2]`. ✓

Why bother: it's two contiguous arrays (cache-friendly, picklable, no
per-cell objects), and every graph algorithm we write later — flow routing,
BFS, priority-flood — loops over exactly these slices.

### What to build

```python
@dataclass(frozen=True)
class MeshGeometry:
    width: float
    height: float
    sites: np.ndarray             # (n, 2) float64
    neighbor_indices: np.ndarray  # (total_edges,) int32
    neighbor_offsets: np.ndarray  # (n + 1,) int32

    @property
    def n_cells(self) -> int: ...
    def neighbors_of(self, i: int) -> np.ndarray: ...   # the slice above
```

Plus a helper `csr_from_lists(list[set[int]]) -> tuple[indices, offsets]`
(hint: `np.cumsum` builds offsets from per-cell counts).

**Check:** hand-build the 3-cell example above with `csr_from_lists` and assert
`neighbors_of` returns what you expect for all three cells.

---

## Step 3 — Port the torus Voronoi builder (2–3 h)

### The lesson first

This is the one piece of the old code worth keeping nearly as-is —
`geometry/periodic_voronoi.py` is already correct. Before porting it, *read it
until you can explain these three tricks to a rubber duck*:

1. **Jittered grid seeding** (`_generate_jittered_sites`): random points clump;
   a grid is sterile. One random point per grid cell gives even-but-organic.
2. **The 3×3 tiling trick** (`_tile_sites`): scipy's Voronoi doesn't know about
   wrapping, so we copy every site 9 times (shifted by ±width, ±height) and
   build the diagram on the big sheet. The center copy (`index * 9 + 4` — copy
   #4 of each site's 9) then has correct *wrapped* neighbors, because its
   "edge" neighbors are other sites' shifted copies. We keep only center-copy
   adjacency and map copies back to their canonical index.
3. **Lloyd relaxation** (`_lloyd_relax`): move each site to its cell's centroid
   and rebuild; 2 rounds turn jitter into evenly-sized, well-shaped cells
   ("blue noise"). More rounds → more uniform → more sterile.

### What to build

`geometry/mesh.py` with one entry point:

```python
def build_mesh(seed: int, cell_count: int, lloyd_iterations: int,
               width: float, height: float) -> MeshGeometry: ...
```

Port the logic from `periodic_voronoi.py`, but output `MeshGeometry`
(sites as one `(n, 2)` array, adjacency through your `csr_from_lists`) instead
of `MeshCell` objects. Use `numpy` arrays internally where it's natural
(`sites` can be built as an array from the start), but don't force it — the
tiling/Delaunay part is fine as ported.

**Check (REPL):** build `n=500`; assert every cell has ≥ 3 neighbors, adjacency
is symmetric (if `j` in `neighbors_of(i)` then `i` in `neighbors_of(j)` —
write this as a loop, it becomes a real test in step 8), and sites all lie in
`[0, width) × [0, height)`.

---

## Step 4 — Seeded noise without global state (1–2 h)

### The lesson first

The old sampler calls `opensimplex.seed(seed)` — a *module-level global*. Two
samplers can't coexist; importing something that seeds noise silently changes
your world; tests pass or fail depending on import order. Rule: **randomness is
something you hold, not something the module is**.

Second lesson — **sub-seeding**. Many things need independent randomness
(elevation noise, plate drift, leyline placement…). Feeding them all the same
`Random(seed)` *in sequence* means adding one `rng.random()` call in stage 2
reshuffles every stage after it. Instead, each named purpose derives its own
seed from the world seed:

```python
def subseed(seed: int, name: str) -> int:
    return zlib.crc32(f"{seed}:{name}".encode()) & 0x7FFFFFFF
```

Why `crc32` and not Python's `hash()`: `hash()` is salted per process by
design — it would give a *different world for the same seed every run*. That's
the kind of bug determinism tests (step 8) exist to catch.

(Keep the two ideas from the old sampler that were *good*: the 4D
torus-mapping — sampling noise on two circles so it wraps seamlessly both
ways — and per-field domain offsets. Port, don't reinvent.)

### What to build

In `noise/rng.py`:

```python
def subseed(seed: int, name: str) -> int: ...

class NoiseSource:
    """Owns one OpenSimplex instance; replaces the global-seed sampler."""
    def __init__(self, seed: int, width: float, height: float) -> None:
        self._noise = opensimplex.OpenSimplex(seed)   # instance, not seed()
    def sample(self, x, y, frequency, offset=(0,0,0,0)) -> float: ...
```

Port `PeriodicSampler.sample`'s body (the cos/sin 4D mapping) onto the
instance. Add a vectorized `sample_array(xs, ys, frequency, offset)` — loop
over the arrays calling `noise4` for now (opensimplex's vector API can come
later; the *interface* being array-shaped is what matters). Port `FractalField`
(`noise/field.py`) to take a `NoiseSource` — its FBm octave loop is already
fine.

> If `opensimplex.OpenSimplex(seed)` isn't exposed in the installed version,
> check `dir(opensimplex)` — the class exists in 0.4.x. Worst case, pin the
> version that has it.

**Check (REPL):** two `NoiseSource(42, ...)` give identical samples;
`NoiseSource(42)` ≠ `NoiseSource(43)`; sample at `x=0` equals sample at
`x=width` (seamless wrap — this becomes a test in step 8).

---

## Step 5 — Context, pipeline shell, placeholder stage (1–2 h)

### What to build

New `context.py` and `pipeline.py` (replacing the old ones at the end of the
phase):

```python
@dataclass
class WorldContext:
    config: WorldgenConfig
    geometry: MeshGeometry
    fields: MeshFields
    def seed_for(self, name: str) -> int:        # subseed(config.seed, name)
    def noise_for(self, name: str) -> NoiseSource:
```

A `Stage` protocol (`run(ctx) -> None` — stages mutate `ctx.fields` in place
now; returning ctx was ceremony), and a pipeline that builds geometry, allocates
fields, and runs an ordered stage list.

Then your first stage, `PlaceholderElevationStage`: fill
`fields.elevation` with 3-octave FBm via a `FractalField` from
`ctx.noise_for("elevation")`, then normalize to [0, 1] —
`(z - z.min()) / (z.max() - z.min())` *as one array expression, no loop* (your
first real SoA move). Set `is_land = elevation > 0.6` so the viewer has two
things to show. This stage is scaffolding — Phase 1 deletes it.

**Check:** a 5-line script builds a world at `cell_count=2000` and prints
`elevation.min()`, `.max()`, `is_land.mean()` (≈ land fraction). Runs in
well under a second.

---

## Step 6 — The bake: mesh → grid in four lines (1–2 h)

### The lesson first

The grid (size×size tiles) samples the mesh by "which cell is nearest to this
tile's center?" — 10,000 nearest-neighbor queries. Brute force is 10,000 ×
12,000 distance checks; a **KD-tree** (a binary tree that splits space by
coordinates) answers each query in ~log n. scipy has it: `scipy.spatial.cKDTree`.

Torus subtlety: a tile at the map's left edge may be nearest to a cell at the
*right* edge. Same fix as the Voronoi: build the tree over the 3×3 tiled sites
and map hits back with `% n_cells`... or — cheaper and just as correct — query
with `cKDTree(sites, boxsize=[width, height])`, scipy's built-in periodic mode.
Use `boxsize`. (Knowing the manual trick is still worth something: it's the
same idea you already ported in step 3.)

Then the punchline that justifies the whole refactor. Once you have
`nearest: np.ndarray` of shape `(size*size,)` — the cell id under each tile —
copying *any* field to the grid is **fancy indexing**:

```python
grid_elevation = fields.elevation[nearest]
```

`array[array_of_indices]` gathers all 10,000 values in one C call. The old
55-line `GridDeriveStage` becomes that one line per field — and with the
generic `dataclasses.fields` iteration from step 1, one loop for *all* fields,
forever, including ones that don't exist yet.

### What to build

In `bake.py`:

```python
def nearest_cell_per_tile(geometry: MeshGeometry, size: int) -> np.ndarray: ...
def bake_to_grid(fields: MeshFields, nearest: np.ndarray) -> GridFields: ...
```

with `GridFields` mirroring `MeshFields` (it can literally be generated from
the same field list — keep them as one shared definition if you can see how;
separate is fine too). Tile centers are at `((x + 0.5) / size * width)`.

**Check (REPL):** bake the step-5 world to a 100×100 grid; assert
`grid.elevation.shape == (10000,)` and the land fraction roughly matches the
mesh's.

---

## Step 7 — Point the viewer at it (2–3 h)

`scripts/worldgen_render.py` is the layer→color logic; `view_worldgen.py` is
the TUI shell. Update `generate_world` to run the new pipeline and the
rasterizer to read `GridFields` arrays instead of `tile.position.*` attributes.
Trim `LAYER_ORDER` to what exists (elevation, land/water) — layers come back
one by one as later phases land, and *that's the point*: by the end of Phase 0
you have a window into every future algorithm, one keypress per layer.

**Check:** `uv run python scripts/view_worldgen.py`, look at noise-blob
elevation in glorious terminal pixels. It's a placeholder; it should still feel
good.

---

## Step 8 — First invariant tests (1–2 h)

Create `test/worldgen/test_foundations.py`. Three tests, all small worlds
(`cell_count=500`, fast):

1. **Determinism** — build the same seed twice; `np.array_equal` on every
   field, sites, and adjacency. *This is the most valuable test in the whole
   project*: it catches global-state leaks, accidental `hash()` use, and
   set-iteration-order bugs, none of which announce themselves otherwise.
2. **Adjacency symmetry** — your step-3 loop, formalized.
3. **Wrap continuity** — `NoiseSource` agrees at `x=0`/`x=width` and
   `y=0`/`y=height` for several offsets and frequencies.

**Check:** `uv run pytest test/worldgen/ -q` — green.

---

## Step 9 — Delete the old world (30 min)

Remove: `data.py` (the dataclasses the new modules replaced), `stages/` (the
placeholder pipeline supersedes it), old `context.py`/`pipeline.py`,
`noise/sampler.py`'s global-seed path, `geometry/periodic_voronoi.py` (absorbed
into `mesh.py`), `geometry/grid_index.py` / `mesh_index.py` (absorbed into
`bake.py`), `config/biome_centers.py` and the anchor/savagery/alignment configs
(their replacements arrive in later phases — config entries can be re-added
when the stage that reads them exists).

Expect `src/service/world.py` to still be broken — it was before (it imports
`DungeonData`, which hasn't existed for months) and it's explicitly out of
scope. `grep -rn "worldgen" src/ scripts/` and make sure *scripts* and *tests*
are the only living consumers.

**Check:** viewer runs, tests pass, `git status` shows a satisfying amount of
red.

---

## Exit criteria

- [ ] `MeshFields` / `MeshGeometry` / `GridFields` exist; no `MeshCell` anywhere
- [ ] `build_mesh` produces CSR adjacency on the torus
- [ ] No `opensimplex.seed()` global anywhere; all randomness via `subseed`
- [ ] Pipeline runs placeholder elevation; viewer shows it
- [ ] Bake is generic fancy-indexing, not field-by-field copies
- [ ] 3 invariant tests green; old modules deleted

**Then Phase 1** (the fun one): plates, uplift, and the erosion solver — where
the placeholder stage dies and real terrain appears in the viewer you just
built.
