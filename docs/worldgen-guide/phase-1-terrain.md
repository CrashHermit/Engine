# Phase 1 — Terrain: Plates, Uplift, and Erosion

*Prerequisite: Phase 0 complete (fields, mesh, RNG, bake, viewer, tests green).
This is the longest phase and the one where you learn the most. Take it slow;
every step ends with something visible in the viewer.*

**What Phase 1 delivers:** real terrain. The placeholder noise stage dies;
in its place: a plate map, an uplift field, and an erosion loop that carves
mountain ranges and valley networks. Ends with the finalize stage (sea level,
landmasses, coast distance, slope) producing the elevation contract
(`[-1, 1]`, 0 = sea level).

**Concepts you'll learn:** multi-source flood fill, vector math on a torus,
priority queues (heaps), topological ordering on a flow tree, implicit vs
explicit numerical solvers, and the art of tuning a simulation by eye.

---

## Step 1 — New fields (15 min)

Add to `MeshFields` (one line each — Phase 0's payoff):

```python
plate_id: np.ndarray      # int32   — which plate owns the cell
uplift: np.ndarray        # float64 — tectonic push-up rate
z_route: np.ndarray       # float64 — "filled" elevation used for flow routing
receiver: np.ndarray      # int32   — downstream cell id (-1 = none / base level)
drainage: np.ndarray      # float64 — upstream cell count (uniform-rain area)
slope: np.ndarray         # float64
coast_distance: np.ndarray
landmass_id: np.ndarray   # int32
landmass_class: np.ndarray  # int8: 0 ocean, 1 island, 2 landmass, 3 major
```

Add a `PlatesConfig` and `ErosionConfig` to the config module as you go —
every magic number you're about to write belongs there.

---

## Step 2 — Partition the mesh into plates (2–3 h)

### The lesson first

We want ~8–15 contiguous regions covering the mesh. The textbook tool is
**multi-source BFS**: drop K seeds, grow them outward one ring at a time until
every cell is claimed. Problem: BFS grows perfectly round blobs — plate borders
come out as neat circles, and your mountain ranges will look like crop circles.

The fix is one line of concept: grow with a **priority queue ordered by
randomized distance** instead of a FIFO queue. Each frontier edge gets cost
`1 + noise`, so growth is mostly-even but raggedy — organic borders for free.
(You'll use the exact same heap pattern again in step 5, which is why we learn
it here.)

How a heap works, in one paragraph: `heapq` keeps a list arranged so the
smallest item is always `heappop`-able in O(log n). You push `(priority, item)`
tuples. That's it — a to-do list that always hands you the cheapest task next.

### What to build

```python
def build_plates(geometry, n_plates, seed) -> np.ndarray:   # plate_id per cell
```

1. Pick `n_plates` seed cells (use `rng.sample`; spacing niceties optional —
   randomness is fine here).
2. Push `(0.0, seed_cell, plate)` for each onto a heap.
3. Pop; if the cell is unclaimed, claim it for the plate, then push every
   unclaimed neighbor with priority `current + 1.0 + rng.random() * R`
   (`R ≈ 2.0` — the raggedness knob).
4. Stop when the heap is empty. Every cell is claimed (the mesh is connected).

**Check (viewer):** add a `plates` layer — color by `plate_id % len(palette)`.
You should see a cracked-eggshell world. Re-run with a different seed; plates
move. With `R = 0` you should see the boring round version — look at both so
you *see* what the noise buys.

---

## Step 3 — Plate personalities (1 h)

Each plate gets, from `rng = random.Random(ctx.seed_for("plates"))`:

- **type**: continental with probability `continental_fraction` (~0.45).
  Continental plates ride high (base uplift ≈ 1.0), oceanic ride low (≈ 0.0).
  Continents will emerge as *unions of adjacent continental plates* — which is
  why their shapes won't be round.
- **drift**: a random unit vector `(cos θ, sin θ)` — the direction the plate
  "moves." We never actually move anything; drift exists only to be compared
  across boundaries in the next step.

Initialize `uplift[:] = base_uplift[plate_id]` (fancy indexing — a lookup table
indexed by an array; same trick as the bake).

**Check (viewer):** an `uplift` layer. Continental plates light, oceanic dark.

---

## Step 4 — Boundary collisions → mountain belts (3–4 h)

### The lesson first

Real mountain ranges are elongated because they form *along* plate boundaries.
We get that by asking, at every boundary, "are these two plates moving toward
each other?" — a dot product:

For neighboring cells `i`, `j` on different plates, let `d` be the unit vector
from `i`'s site to `j`'s site. **Torus subtlety:** compute the difference with
the *minimum-image rule* first — for each axis, if `|dx| > width/2`, the short
way is around the seam: `dx -= width * round(dx / width)`. (Write
`torus_delta(a, b, width, height)` as a helper — you will use it in every
remaining phase.)

Convergence = `(drift[plate_i] - drift[plate_j]) · d`. Positive → the plates
close in → **collision** (uplift spike). Negative → they separate → **rift**
(uplift dip). Near zero → they slide past → nothing much.

A one-cell-wide spike isn't a mountain range, so we **smear** it: BFS outward
from boundary cells a few hops, with the boundary intensity decaying per hop,
keeping the max where smears overlap. Multiply by `1 + noise` so belts pulse
instead of being uniform sausages.

### What to build

```python
def apply_boundary_uplift(geometry, plate_id, drifts, uplift, config, noise) -> None
```

1. Find boundary cells: any cell with a neighbor on another plate. For each
   boundary *edge*, compute convergence; a cell's raw intensity is the max
   convergence over its cross-plate edges (and min for rifts).
2. Multi-source BFS from boundary cells (plain BFS is right this time — we
   *want* smooth falloff), carrying `intensity * falloff^hops` for
   `belt_width` hops (~3–5).
3. `uplift += belt_strength * smeared_collision * (1 + 0.5 * belt_noise)` and
   `uplift -= rift_strength * smeared_rift`; clamp at ≥ 0 *after* adding a
   small noise floor everywhere (`0.05 * fbm`) so oceanic plates aren't
   billiard-flat.

**Check (viewer):** the `uplift` layer should now show bright elongated belts
along some plate borders (the converging ones), dark seams along others. This
image *is* your future mountain map — stare at it. If belts are everywhere or
nowhere, your drift vectors or dot product sign is off.

---

## Step 5 — Flow routing with priority-flood (3–4 h)

### The lesson first

Erosion needs to know where water goes. For most cells that's easy: the
steepest-descent neighbor (the **receiver**). But terrain has bowls — cells
lower than all their neighbors — and water doesn't stop there, it *fills the
bowl and spills over*. The old code handled this by permanently raising the
terrain (cells in bowls had their `z` overwritten). That destroys the very
feature it's routing around. We do it right:

**Priority-flood (Barnes 2014)** computes, without mutating `z`, the *water
surface* `z_route`: for every cell, the level water would need to reach to flow
from that cell to the ocean. For normal cells `z_route == z`; inside bowls
`z_route` is flat at the spill level. The algorithm is beautifully small:

1. Push all *ocean* cells onto a heap keyed by their `z` (ocean = base level;
   on the first erosion iteration, before sea level exists, use "all boundary…"
   — we don't have boundaries on a torus, so: use the lowest `p`-percentile of
   `z` as provisional ocean — `ErosionConfig.base_level_fraction ≈ 0.1`).
2. Pop the lowest cell, mark visited, set
   `z_route[cell] = max(z[cell], z_route[popped_from])` — i.e., water can't
   descend below the level it arrived at.
3. Push unvisited neighbors keyed by *their* `z_route`-so-far
   (`max(current_level, z[neighbor])`).
4. Repeat until empty. Every cell is reached in ascending water-level order.

This is the same heap from step 2 wearing a hydrology hat.

Receivers are then trivial: each cell's receiver is its lowest-`z_route`
neighbor, if lower than itself; cells with no lower neighbor on the *routed*
surface are base level (`receiver = -1`). Inside a filled bowl, `z_route` ties
get broken by tiny `+ epsilon * hops` during the flood (add it when you set
`z_route`) so water drifts toward the spill instead of standing in a flat
puddle of equal values.

### What to build

```python
def priority_flood(geometry, z, base_cells) -> np.ndarray          # z_route
def compute_receivers(geometry, z_route) -> np.ndarray             # int32, -1 = pit/base
```

**Check (test, not viewer):** generate any terrain (even the old placeholder
noise); assert that following `receiver` from every cell reaches a base-level
cell in ≤ n steps (no cycles, no dead ends except base). This becomes the
permanent "water always reaches the ocean" invariant.

---

## Step 6 — Drainage accumulation (1 h)

### The lesson first

`drainage[i]` = how many cells drain through `i` (uniform rain: every cell
contributes 1). The trick is processing order: you must add a cell's total to
its receiver only after the cell itself is complete — i.e., process from
high to low. Sorting by `z_route` descending *is* a valid topological order of
the flow tree, because receivers are always lower. One `np.argsort`, one loop:

```python
order = np.argsort(z_route)[::-1]
drainage[:] = 1.0
for i in order:
    r = receiver[i]
    if r >= 0:
        drainage[r] += drainage[i]
```

(This loop stays in Python — it's inherently sequential. 12k iterations is
nothing.)

**Check (viewer):** add a `drainage` layer using `log(drainage)` for color
(raw values span 1 to thousands — logs make rivers visible). Even on noise
terrain you should see branching tree veins. That branching structure is the
thing erosion is about to carve into the rock.

---

## Step 7 — The implicit stream-power solver (3–4 h)

### The lesson first

The physics: `dz/dt = U − K · A^m · S` (uplift up, water-carving down; `A` =
drainage, `S` = slope toward receiver, `m ≈ 0.5`). The naive update
("explicit") computes erosion from current heights and subtracts — and
explodes if a cell erodes past its receiver in one step, forcing tiny steps.

The **implicit** method (Braun & Willett 2013) instead asks: "what is my *new*
height, given my receiver's *already-updated* new height?" Solving the
one-cell equation for `z_new` gives a closed form:

```
f        = dt * K * drainage[i]^m / dist(i, receiver)
z_new[i] = (z[i] + dt * U[i] + f * z_new[receiver]) / (1 + f)
```

Look at what that formula *does*: it's a weighted average of "where I'd be
with pure uplift" and "my receiver's new height." It can approach the receiver
but never overshoot — that's why it's unconditionally stable at any `dt`.
The only requirement is processing order: receivers before donors — the same
ascending-`z_route` order you already have (use `np.argsort(z_route)`, not
reversed).

Base-level cells (`receiver == -1`) just take uplift (or stay fixed; pick one,
it converges either way). Cells under lake water (`z < z_route`) skip erosion —
submerged rock doesn't channel.

### What to build

```python
def stream_power_pass(z, z_route, receiver, drainage, uplift, geometry, cfg) -> None
```

with `cfg`: `dt`, `K`, `m`. Distances between sites via your `torus_delta`.

**Check (REPL):** run a single pass on placeholder terrain. Nothing should be
NaN; `z` should change *smoothly* (plot/print a histogram before and after).
Big `dt` should not explode — that's the whole point. Try `dt` 10× larger and
confirm it still doesn't.

---

## Step 8 — Hillslope diffusion (1 h)

Stream power only touches channels; ridges between them would sharpen into
knife edges forever. Real slopes shed material downhill ("hillslope
diffusion"). The cheap version: every cell relaxes a little toward its
neighbors' mean:

```python
z[i] += diffusion * (mean(z[neighbors_of(i)]) - z[i])
```

`diffusion ≈ 0.05–0.15`. Compute all the deltas first, then apply (otherwise
early cells influence later ones within a pass — order-dependence is a
determinism bug *and* a subtle directional bias). This is your CSR adjacency's
second customer.

**Check:** run 20 diffusion-only passes on noise; it should visibly blur.

---

## Step 9 — The loop, and learning to tune (2–4 h, mostly looking)

Assemble `ErosionStage`:

```
z = uplift * initial_scale + small_noise        # starting guess
repeat cfg.iterations (start ~50):
    z_route  = priority_flood(...)
    receiver = compute_receivers(...)
    drainage = accumulate(...)
    stream_power_pass(...)
    diffuse(...)
```

Now delete `PlaceholderElevationStage`. Pipeline order so far:
`Mesh → Plates → BoundaryUplift → Erosion`.

Then spend real time in the viewer. This is a skill, not a chore — every knob
has a visual signature, and you should learn to read them:

- **K too high** (or uplift too low): everything erodes to mush — low rounded
  nothing. **K too low**: uplift wins, plateaus with no valleys.
- **dt too low / iterations too few**: terrain still looks like the uplift map
  (you'll recognize it — you stared at it in step 4).
- **diffusion too high**: melted ice cream. **Too low**: spiky ridge noise.
- The goal image: mountain *ranges* where your collision belts were, with
  branching valley systems cut into their flanks, draining toward the low
  plates.

Tune `K`, `dt`, `iterations`, `diffusion`, `m` until you'd screenshot it.
Write the winning numbers into `ErosionConfig` defaults.

---

## Step 10 — Finalize: the elevation contract (2–3 h)

The last stage of the terrain group, `TerrainFinalizeStage`:

1. **Sea level by percentile**: `sea = np.quantile(z, 1 - target_land_fraction)`;
   `is_land = z >= sea`.
2. **Piecewise normalize** (the contract from the plan): land maps to `(0, 1]`
   against the highest peak, ocean to `[-1, 0)` against the deepest floor,
   sea level pinned at exactly 0. Two masked array expressions — no loops.
3. **Landmass labeling**: connected components over land cells (plain BFS with
   your CSR adjacency — third customer); sizes; classify
   island/landmass/major by fraction thresholds (port the old
   `LandmassStage` logic — it was fine).
4. **Coast distance**: multi-source BFS from all coastal land cells (hops).
5. **Slope**: per cell, `max(z[i] - z[neighbors]) / distance` — steepest drop.

**Check (viewer + tests):**
- Viewer `elevation` layer with a sea-floor palette below 0 and land palette
  above — this is the money shot of the whole phase.
- Tests to add: land fraction within ±3% of target; elevation within
  `[-1, 1]` with `min < 0 < max`; downhill invariant from step 5 now running
  on final terrain; determinism still green (run it — step 2's `rng.sample`
  and heap tie-breaking are exactly where nondeterminism sneaks in; if it's
  red, your heap needs deterministic tie-breaks: push `(priority, cell_id)` so
  ties break by id).

## Exit criteria

- [ ] Plate, uplift, drainage, elevation layers in the viewer
- [ ] Mountain ranges along convergent boundaries with carved valleys
- [ ] No terrain mutation for routing (`z` vs `z_route` separate)
- [ ] Elevation contract: `[-1,1]`, 0 = sea, piecewise normalized
- [ ] Invariants green: downhill, land fraction, ranges, determinism

**Phase 2** builds the atmosphere on top of this: insolation rings,
temperature, wind, and the moisture transport that turns your mountains into
rain shadows.
