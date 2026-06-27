# Worldgen Rivers & Lakes — Flow/Pool Investigation

## Symptom

In the worldgen viewer the water layers don't read as rivers. Rivers appear as
short, chunky blue blobs rather than lines that flow down valleys from highland
to sea, and lakes don't read as water pooling in basins. The complaint: *"it's
supposed to flow and pool based on geography — these don't at all."*

This document records what the flow/pool logic is actually doing, the evidence,
and the root causes — shallowest (cheap to fix) to deepest (the real problem).

## What is NOT broken

The core hydrology is sound. Verified on seed 0 (mesh = 6400 cells, 1:1 with the
80×80 tile grid, so render coarseness is not a factor):

- **Water flows downhill.** Following the `receiver` flow tree, `z_route` never
  increases downstream (0 cells flow uphill in routing elevation). The ~2.3% of
  receivers that rise in *raw* elevation are lake spillways crossing
  priority-flood-filled depressions — expected.
- **Discharge accumulates correctly.** The longest land drainage path (19 cells)
  builds monotonically head→mouth: discharge `0.6 → 1.1 → 1.6 → 3.1 → … → 35.3`,
  elevation `0.237 → … → 0.074`. That *is* a real river flowing by geography.
- **Rivers stay on land / lakes sit in depressions.** 0 river cells in ocean
  (mesh-side); lake cells are exactly the filled-depression cells
  (`z_route > elevation + ε`).

So the river/lake code faithfully traces the terrain it is given.

## Root causes (shallow → deep)

### 1. Headwaters are clipped by the percentile threshold — *tuning*

`classify_rivers` keeps cells with `discharge ≥ quantile(land_discharge, 1 −
river_fraction)`, with `river_fraction = 0.05` (top 5%). Land discharge is
extremely skewed (p50 = 0.7, p90 = 2.7, p95 = 3.9, p99 = 15.6, max = 37.8), so
the 5% threshold (≈3.9) only fires where flow is *already* large — near the
mouth. The 19-cell river above renders as ~13 cells: its top six headwater cells
(discharge 0.6–3.4) fall below threshold and are dropped. Every river loses its
upstream half.

**Layer:** `src/worldgen/water/rivers.py::classify_rivers`

### 2. Lakes sever rivers into stubs — *design*

`is_river = is_land & ~is_lake & (discharge ≥ threshold)`. A river that flows
into a lake and out the far side is cut into two disconnected rivers, because the
lake cells in between are excluded. On the longest path, a 2-cell lake at indices
10–11 splits one geographic river into two. This is why the river-length
histogram is dominated by 1- and 2-cell fragments (51 "rivers" on seed 0, most
length 1–2). Hydrologically defensible, but visually it shatters continuous
watercourses.

**Layer:** `src/worldgen/water/rivers.py::classify_rivers` / `extract_rivers`

### 3. The terrain has no interior — *the dominant cause (terrain/erosion)*

Even ignoring (1) and (2), rivers can't be long because the land has nowhere for
water to travel. Across seeds 0/1/2 the largest landmass is 2000–3000 cells, yet
its **maximum distance from the coast is only 8–9 cells, mean ≈2**. A compact
landmass that size should have interior cells 20+ hops deep. Mean coast-distance
of ~2 means the continents are thin, stringy, fractal tangles where essentially
every land cell is coastal. Consequences on seed 0:

- Land-only drainage path length: mean 3.5, p90 7, max 19.
- 25% of land cells drain *directly* into the ocean in a single hop.

There are no sustained regional gradients to collect flow into long trunk
rivers, and few enclosed basins to pool sizeable lakes. The river/lake logic is
correctly draining a terrain that simply has no river-supporting structure.

**Layer:** terrain shaping — uplift / erosion / landmass generation
(`src/worldgen/terrain/*`).

| Seed | Land cells | Biggest landmass | Coast-dist max | Coast-dist mean |
|------|-----------:|-----------------:|---------------:|----------------:|
| 0    | 2301       | 2033             | 8              | 1.9             |
| 1    | 3018       | 2991             | 9              | 2.4             |
| 2    | 2562       | 1926             | 9              | 2.0             |

## Already fixed in this branch

A genuine stamping bug surfaced while building the new viewer layers and is
fixed: `bake/rivers.py::_stamp_disk_around` stamped `is_river = True` onto every
tile in the disk with no land check, so river mouths (up to `max_w = 8` wide)
spilled fat disks of "river" into the ocean — 63% of river tiles on seed 0 were
in the sea. It now skips ocean tiles. New `Rivers` and `Lakes` viewer layers were
also added so this network can be inspected at all (previously only the
all-land `Discharge` accumulation field was exposed).

## Recommended fix plan

**A. River logic (causes 1 + 2) — contained, ~1 stage:**
- Replace the bare percentile cut with an upstream trace: find trunk cells by
  threshold, then walk the receiver tree upstream (following the
  highest-discharge inflow at each junction) to extend each river to its source.
  This yields full-length head→mouth rivers regardless of the skew.
- Let rivers pass *through* lakes for continuity (treat a river→lake→river
  sequence as one watercourse for rendering/identity), instead of severing.

**B. Terrain shape (cause 3) — the real fix, larger:**
- The continents need deep interiors. Investigate why coast-distance maxes out at
  ~8: likely the uplift/landmass mask produces stringy noise rather than solid
  cratons. Candidate levers: stronger low-frequency continental mask, fewer/larger
  landmasses, erosion that carves sustained valleys, or an explicit interior
  bonus. Long rivers and real lake basins follow once interiors exist.

Recommendation: do **B** — without it, **A** only makes the short rivers denser,
not longer. **A** is still worth doing but is cosmetic until the terrain hosts
real drainage. (**A** alone is the cheap stopgap; **B** is the actual answer to
"flow and pool based on geography.")

## How to reproduce

```bash
# Visual: cycle to the Water group → Rivers / Lakes layers
uv run python scripts/view_worldgen.py --seed 0 --size 80

# Export the layers
uv run python scripts/view_worldgen.py --seed 0 --size 80 --layer rivers --export rivers.png
uv run python scripts/view_worldgen.py --seed 0 --size 80 --layer lakes  --export lakes.png
```

The diagnostics in this doc come from `WorldgenPipeline().run_debug(seed=…,
size=80)`, inspecting `ctx.fields` (`receiver`, `discharge`, `z_route`,
`is_land`, `is_lake`, `coast_distance`, `landmass_id`) and `ctx.outputs.rivers`.
