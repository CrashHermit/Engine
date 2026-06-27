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

### 3. The world was too small to *have* interior — *the dominant cause (scale, not erosion)*

Even ignoring (1) and (2), rivers can't be long because the land has nowhere for
water to travel. Across seeds 0/1/2 the largest landmass is 2000–3000 cells, yet
its **maximum distance from the coast is only 8–9 cells, mean ≈2**. Mean
coast-distance of ~2 means the continents are thin, stringy tangles where
essentially every land cell is coastal. On seed 0: land-only drainage paths
average 3.5 cells (p90 7, max 19), and 25% of land drains *directly* into the
ocean in a single hop.

| Seed | Land cells | Biggest landmass | Coast-dist max | Coast-dist mean |
|------|-----------:|-----------------:|---------------:|----------------:|
| 0    | 2301       | 2033             | 8              | 1.9             |
| 1    | 3018       | 2991             | 9              | 2.4             |
| 2    | 2562       | 1926             | 9              | 2.0             |

**This is a scale mismatch, not a shape or erosion defect.** `PlatesConfig.n_plates
= 35` is fixed independent of world size, and the continental interior ramp
(`continental_freeboard` / `freeboard_reach = 0.06` of span) only builds an
interior when there are enough cells across a plate to ramp into. The diagnostics
above were taken at **size 80** — the old viewer default — which crams 35 plates
into an 80-cell torus, so each continent is ~13 cells wide and has no interior.
The config comment at `worldgen_config.py:43-48` predicts exactly this: *"only the
boundary belts surface and land reads as a stringy skeleton."*

The same pipeline, same seed, just larger, produces real rivers — interiors and
drainage scale straight up with world size until coast-distance plateaus around
the per-plate limit:

| size | cells  | coast-dist max / mean | longest drainage path | top-3 river lengths |
|-----:|-------:|----------------------:|----------------------:|---------------------|
| 80   | 6,400  | 8 / 1.9               | 19                    | 14, 8, 7            |
| 160  | 25,600 | 24 / 5.5              | 70                    | **60, 35, 32**      |
| 240  | 57,600 | 23 / 6.3              | 70                    | **60, 54, 52**      |

Erosion is **not** the limiter: it already runs 50 iterations at `K = 0.3`
(`ErosionConfig`), and it carves valleys into existing land rather than creating
interior. The fix is to view/generate at gameplay scale, not to erode harder.

**Layer:** world size / `MeshConfig` density vs `PlatesConfig.n_plates` — not a
bug in the water or terrain stages.

## Fixed in this branch

1. **Ocean-spill stamping bug.** `bake/rivers.py::_stamp_disk_around` stamped
   `is_river = True` onto every tile in the disk with no land check, so river
   mouths (up to `max_w` wide) spilled fat disks of "river" into the ocean — 63%
   of river tiles on seed 0 were in the sea. It now skips ocean tiles.
2. **New `Rivers` and `Lakes` viewer layers** so the network can be inspected at
   all — previously only the all-land `Discharge` accumulation field was exposed.
3. **Viewer default size 80 → 1000** (cause 3). The preview now matches the
   gameplay world scale (`WorldgenConfig.size = 1000`), so rivers and lakes show
   up as they actually exist in play. Trade-off: a size-1000 world hits the mesh
   cap (400k cells) and the full 50-iteration erosion loop, so a single
   generation takes minutes — pass `--size 160` for fast interactive browsing.
4. **`RiverConfig.max_w` 8.0 → 3.0** (cause 2's cosmetic tail). Trunk rivers were
   clamped to 8 tiles wide, which read as blobs; 3 renders them as thin lines.

Causes 1 and 2 (headwater clipping by the percentile threshold; lakes severing
rivers) remain as *tuning/design* choices, not bugs. If we later want
full-length head→mouth rivers regardless of discharge skew, the contained fix is
to extend each classified river upstream along its receiver tree (following the
largest-discharge inflow at each junction) and let rivers pass *through* lakes
for continuity instead of being cut. Left as a follow-up.

## How to reproduce

```bash
# Visual: cycle to the Water group → Rivers / Lakes layers
uv run python scripts/view_worldgen.py --seed 0                # default size 1000 (slow)
uv run python scripts/view_worldgen.py --seed 0 --size 160     # fast browsing

# Export the layers
uv run python scripts/view_worldgen.py --seed 0 --size 160 --layer rivers --export rivers.png
uv run python scripts/view_worldgen.py --seed 0 --size 160 --layer lakes  --export lakes.png
```

The diagnostics in this doc come from `WorldgenPipeline().run_debug(seed=…,
size=…)`, inspecting `ctx.fields` (`receiver`, `discharge`, `z_route`,
`is_land`, `is_lake`, `coast_distance`, `landmass_id`) and `ctx.outputs.rivers`.
