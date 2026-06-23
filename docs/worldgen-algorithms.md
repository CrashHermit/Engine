# Worldgen Algorithms

A step-by-step walkthrough of every algorithm in `src/worldgen`, in pipeline
order, explaining **how** each stage works and **why** it is built that way.
This is the conceptual companion to `src/worldgen/README.md` (which is the quick
stage/field index) and the phase design docs under `docs/worldgen-guide/`.

---

## 0. Principles

A few rules shape every algorithm below; they explain a lot of the "why".

- **Pure function of `(seed, size, config)`.** Generation never reads a clock,
  global RNG, or the filesystem. Every stochastic choice draws from a sub-seed
  derived from the master seed (`ctx.seed_for("name")`), so the same inputs
  always reproduce the same world, bit for bit. This is what the determinism
  test suite locks down.
- **Simulate on a mesh, ship a grid.** All physics runs on an irregular
  Voronoi mesh (~12k cells) wrapped on a torus. The gameplay product is a
  `size × size` square grid baked from the mesh at the very end. The mesh is an
  internal intermediate; it never ships.
- **Everything wraps (a torus).** There are no map edges. Distances, noise, and
  neighbor lookups all use minimum-image wrapping, so the north edge meets the
  south and the east meets the west seamlessly.
- **Causally consistent, not pretty.** Stages run in the order real processes
  happen. Volcanoes and mountains are raised *before* erosion so rivers carve
  them realistically, rather than being stamped on as decoration afterward.
- **Each stage reads its inputs and writes its outputs on the context.** Stages
  are independent and ordered; there is exactly one deliberate cross-stage
  coupling (caldera crater-lakes), called out where it occurs.

The pipeline order is defined in `pipeline.py::_build_stages`. The sections
below follow that order.

---

## 1. Geometry — the torus Voronoi mesh

**File:** `geometry/mesh.py` · **Why a mesh:** a regular square grid bakes its
own anisotropy into rivers and coastlines (everything wants to run along the 4
axes). An irregular Voronoi mesh has no preferred direction, so terrain and
water look organic.

**Steps (`build_mesh`):**

1. **Jittered sites (`_generate_jittered_sites`).** Lay down one point per cell
   of a coarse `rows × cols` grid, each randomly jittered within its cell. This
   gives an *even but organic* point cloud — better than pure random (which
   clumps) and better than a regular grid (which aligns).
2. **Lloyd relaxation (`_lloyd_relax`, ×`lloyd_iterations`).** Move each site to
   the centroid of its Voronoi cell. A couple of passes even out the cell sizes
   so no cell is a sliver, without over-regularizing into a grid.
3. **Periodic adjacency (`_build_neighbor_graph`).** To make the mesh wrap, the
   sites are replicated on a 3×3 tile (`_tile_sites`) and a Delaunay
   triangulation is built over the whole tile. Two cells are neighbors if a
   Delaunay edge connects them, where at least one endpoint is in the central
   tile (`% 9 == 4`). This yields correct wraparound neighbors at the seams.
4. **CSR packing (`csr_from_lists`).** The per-cell neighbor sets are flattened
   into two arrays — `neighbor_indices` (all neighbors concatenated) and
   `neighbor_offsets` (where each cell's slice starts). `neighbors_of(cell)` is
   then a zero-copy slice. Almost every later stage iterates this CSR.

**Output:** `MeshGeometry` (site positions + CSR adjacency + torus dimensions).

---

## 2. Noise — deterministic fractal fields

**Files:** `noise/rng.py`, `noise/field.py`. Worldgen uses OpenSimplex noise
wrapped in a `FractalField` (fractal Brownian motion: several octaves of noise
summed at halving amplitude / doubling frequency). Each named field gets its own
sub-seed so, e.g., the wind turbulence and the uplift floor are independent but
both reproducible. Sampling is torus-aware so noise wraps. Noise is used for:
organic plate borders, mountain-belt modulation, wind turbulence, insolation
wobble, savagery surprise, and magic valence/floor.

---

## 3. Phase 1 — Terrain genesis

The goal of Phase 1 is a heightfield with continents, mountains, volcanoes, and
a drainage-consistent surface, then a sea level that turns it into land/ocean.

### 3.1 Plates (`terrain/plates.py::build_plates`)

**How:** pick `n_plates` random seed cells, then grow all plates outward
simultaneously with a **min-heap flood** (Dijkstra-like). Each step pops the
lowest-cost frontier cell, claims it for its plate, and pushes its unclaimed
neighbors with cost `+1 + random*growth_raggedness`.

**Why:** simultaneous cost-based growth produces contiguous plates that meet
along natural-looking borders. The random raggedness term keeps borders from
being smooth circles; `growth_raggedness=0` would give round blobs.

**Output:** `plate_id` per cell.

### 3.2 Plate personalities (`terrain/plate_personalities.py`)

For each plate, roll three properties from the seed:

- **Type** — continental (probability `continental_fraction`) or oceanic.
  Continental plates get a high `base_uplift`, oceanic a low one.
- **Drift** — a random unit vector (the plate's motion direction).
- **Density** — oceanic plates are denser (base `1.0`) than continental (`0.0`),
  plus a small `density_jitter`. Density decides **subduction polarity**: at a
  convergent boundary the denser plate sinks. The jitter (< 1.0) only breaks
  ties between same-type plates, so every oceanic plate is denser than every
  continental one, guaranteeing oceanic-under-continental subduction.

Density is rolled in a second pass so adding it didn't perturb the
continental/drift rolls of existing seeds.

### 3.3 Boundary classification (`terrain/boundaries.py`)

**Why it exists:** both boundary-uplift and vulcanism need to know what happens
at every plate edge. Computing that twice risks the two drifting apart, so it is
computed **once** here and shared.

**How (`classify_boundaries`):** walk every cell's neighbors. For each neighbor
on a *different* plate, compute the closing speed
`dot(drift_i − drift_j, direction_to_neighbor)`. Positive = converging,
negative = diverging. Per cell, keep the dominant convergence and the dominant
divergence separately (a cell can border both a converging and a diverging
plate). Tag each with the plate-pair kind:

`CONV_OO / CONV_OC / CONV_CC` and `DIV_OO / DIV_OC / DIV_CC` (O = oceanic,
C = continental). For convergence, also record `is_overriding` — whether *this*
cell sits on the lighter (overriding) plate, from the density comparison.

**Output:** `BoundaryFacts` (convergence, divergence, kinds, overriding flag).

### 3.4 Boundary uplift + continental freeboard (`terrain/boundary_uplift.py`)

Two relief contributions are added to the `uplift` field here.

**Mountain belts and rifts (`apply_boundary_uplift`):**

1. **Smear** the per-cell convergence into a belt with a multi-source BFS
   (`_smear_intensity`): every convergent cell seeds the belt at full strength,
   spreading `belt_width` hops with `belt_falloff` decay per hop, combining by
   max. This widens a one-cell seam into a mountain *range*.
2. Add `belt_strength × smeared_convergence`, modulated by FBm noise so ranges
   aren't uniform.
3. **Rift valleys:** subtract `rift_strength × smeared_divergence` — *except*
   for ocean–ocean divergence (`DIV_OO`), which is left uncut because the
   vulcanism stage raises it into a mid-ocean ridge instead.

**Continental freeboard (`apply_continental_freeboard`)** — *added in the recent
fixes.* Without it, a continental plate is a flat slab sitting right at sea
level: only the boundary belts surface, and the land reads as a stringy skeleton
tracing plate edges while continental interiors drown. Real continental crust is
thick and buoyant — it rides high.

1. BFS the hop distance of every cell from the nearest plate margin
   (`_boundary_hop_distance`).
2. For continental cells, add an edifice that ramps from `0` at the margin to
   `continental_freeboard` in the deep interior:
   `strength × (1 − exp(−distance / reach))`. Distance is converted from hops to
   physical units so the ramp shape is **resolution-independent**.

**Why a ramp (not a flat lift):** making the interior higher than the margins
means the *lowest* continental ground is the coast. When sea level rises it
floods the margins first — continents shrink from their edges, the realistic
behavior — instead of flooding the flat interior into ribbons and inland seas.

### 3.5 Vulcanism (`terrain/vulcanism.py`, `stages/vulcanism.py`)

Runs **before erosion** so volcanic edifices are dissected and drained like all
other terrain. Three mechanisms, all keyed off `BoundaryFacts`:

- **Subduction arcs.** Seed arc potential on the *overriding* plate's trench
  cells (convergent OO/OC, never CC — continent–continent collision is
  amagmatic, "no volcanoes in the Himalayas"). BFS that potential inland,
  staying on the overriding plate, and shape a band peaking `arc_offset` hops
  behind the trench. Adds `arc_uplift × potential` to `uplift`. A continental
  arc forms inland (Andes); an oceanic arc forms an offshore island chain
  (Japan).
- **Hotspots.** Place `hotspot_count` points in plate interiors (biased
  oceanic). For each, walk along the host plate's drift, stamping a trail of
  volcano edifices whose height decays down-trail (`chain_decay**k`). This is an
  island chain laid out in space the way drift lays it out in time — an active
  head and subsiding seamount tail.
- **Rifts / ridges.** Ocean–ocean divergence raises a mid-ocean ridge
  (`ridge_uplift × divergence`) that can breach as islands (Iceland);
  continental rifts get flank volcanism.

Each mechanism contributes to: the `uplift` field (terrain), the `volcanism`
field (present-day activity in `[0,1]`, kept for *all* activity including
submarine ridges — those are the most active places on Earth), and a list of
discrete volcano **candidates**.

**Discrete volcanoes are materialized later** — *changed in the recent fixes.*
The stage used to create `Volcano` objects here, before the coastline existed,
so it stamped a volcano on every submarine boundary cell (100–180 per world).
Now `VulcanismStage` only stashes candidates; `VolcanoesStage` (§3.8) selects
the landmarks once `is_land` is known.

### 3.6 Erosion (`terrain/erosion.py` + `terrain/routing.py`)

The erosion loop runs `iterations` passes; each pass routes water, erodes, and
diffuses.

**Routing (per pass):**

1. **Priority flood (`priority_flood`, Barnes 2014).** Grow a water surface
   `z_route` upward from the lowest cells through a min-heap ordered by
   water-surface height. `z_route` is "the level water must reach to escape this
   cell to the ocean": equal to `z` on slopes, a flat spill level inside basins.
   A tiny `eps × hops` bias is baked in so flat basin floors still have a
   downhill direction. **Why:** this removes the pits that would otherwise trap
   flow, without mutating the real terrain `z`.
2. **Receivers (`compute_receivers`).** Each cell points at its lowest-`z_route`
   neighbor — the downstream flow direction. The `eps` bias guarantees a unique
   downhill even on flats, so no tiebreaking logic is needed.
3. **Drainage (`accumulate_drainage`).** Process cells from high to low
   `z_route`; each passes its accumulated upstream count to its receiver. One
   topological sweep gives every cell its upstream drainage area.

**Erode + diffuse (per pass):**

4. **Stream power (`stream_power_pass`, Braun & Willett 2013).** Process cells
   low→high so each receiver's new height is final before its donors use it.
   Each cell relaxes toward its receiver by an *implicit* update
   `z = (z + dt·uplift + f·z_receiver)/(1+f)`, with `f = dt·K·Aᵐ/L`
   (A = drainage area, L = distance to receiver). **Why implicit:** it is
   unconditionally stable — a cell can approach but never overshoot its receiver,
   so the loop never explodes regardless of `dt`. High-drainage cells (rivers)
   cut faster — that is what carves valleys.
5. **Hillslope diffusion (`diffuse`).** Relax each cell toward its neighbors'
   mean. Deltas are computed for all cells first, then applied together, so the
   pass is order-independent. **Why:** without it, stream power sharpens ridges
   into unreal knife edges; diffusion rounds them.

### 3.7 Finalize (`terrain/finalize.py`)

Turns the raw eroded heightfield into land/ocean plus the derived terrain
fields.

1. **Coast de-speckle (`smooth_elevation`).** A couple of gentle Laplacian
   passes damp cell-scale wiggle so the coastline (cut next) isn't fuzzed with
   one-cell islets and inlets. Run *before* the cut so the land fraction is
   measured on the smoothed field.
2. **Sea level (`apply_sea_level`).** Place sea level at the elevation
   percentile that leaves `target_land_fraction` of cells above it, then
   piecewise-normalize: land → `(0, 1]`, ocean → `[−1, 0)`, sea level pinned at
   `0`. **Why percentile:** it self-adjusts so you get the land fraction you
   asked for regardless of the absolute height distribution.
3. **Landmasses (`label_landmasses`).** BFS connected components of land,
   classified by size into island / landmass / major.
4. **Coast distance (`compute_coast_distance`).** Multi-source BFS inward from
   coastal cells — feeds temperature (maritime moderation) and savagery
   (remoteness).
5. **Slope (`compute_slope`).** Steepest downhill gradient per cell — feeds
   savagery (ruggedness) and flow speed.

### 3.8 Volcanoes — landmark selection (`stages/vulcanism.py::VolcanoesStage`)

*Added in the recent fixes.* Runs **after finalize**, when `is_land` exists, and
turns the stashed candidates into discrete landmark `Volcano` objects
(`select_landmark_volcanoes`):

- Keep candidates that **breached** (on land, or coastal).
- For any chain (arc segment or hotspot trail) that stayed fully submarine, keep
  one **anchor** seamount so the chain is still represented.
- Cap each chain at `max_per_chain` so a long arc is a handful of named cones,
  not a continuous bead-string.

**Why here:** a volcano is a landmark — something you can stand on or sail to.
Selecting against the *finished* terrain drops the submarine clutter and turns
~150 boundary-tracing dots into ~40–60 real edifices, while the `volcanism`
field still carries the full (incl. submarine) activity picture for savagery and
magic.

---

## 4. Phase 2 — Climate

Climate is authored, not simulated over time: a base energy pattern, modified by
terrain. On a torus there is no latitude, so the "latitude" is a chosen axis.

### 4.1 Insolation (`climate/insolation.py`)

The base solar-energy field in `[0,1]`. A cosine in the y-axis gives a hot ring
(`y = 0`) and a cold ring (`y = height/2`) that wrap seamlessly: equator → pole
→ equator around the torus.

*Reshaped in the recent fixes:* a raw cosine lingers at its peaks, so its value
distribution is U-shaped (arcsine) — fat hot/cold extremes, a starved temperate
middle. Raising the cosine to `temperate_bias` (`sign(c)·|c|^bias`, `bias > 1`)
narrows the extreme rings and widens the temperate band — the way most of a
planet is temperate, not polar. `contrast` then sets overall zone spread, and
optional `wobble` warps the ring lines with low-frequency noise so they aren't
laser-straight.

### 4.2 Temperature (`climate/temperature.py`)

`temperature = insolation`, then two corrections:

1. **Lapse rate (mountains are cold).** *Changed in the recent fixes.* Cooling
   is applied to elevation **above a lowland datum** (a percentile of land
   elevation), not above sea level: `−lapse_rate × max(0, elevation − datum)`.
   **Why:** once continents ride high (freeboard), measuring lapse from sea
   level would chill *every* land cell and freeze interiors wholesale. The datum
   makes the continental platform the thermal baseline, so only relief that
   genuinely rises above it (real mountains) cools.
2. **Maritime moderation.** Coasts buffer toward sea temperature with an
   `exp(−coast_distance / maritime_reach)` weight — strong at the shore, fading
   inland. Mild coasts, more extreme interiors.

### 4.3 Wind (`climate/wind.py`)

1. **Zonal belts.** `base_u = −cos(phase)`, `base_v = sin(phase)·meridional`,
   `phase = 2π·y/height·belt_count` — east-west belts that wrap, with a small
   north-south component.
2. **Turbulence.** Add independent FBm per component so belts meander.
3. **Terrain deflection (`deflect_wind`).** Compute the elevation gradient;
   subtract the component of wind blowing into uphill terrain. Wind bends along
   ranges and accelerates through gaps. The deflected vector's length is a
   natural `[0,1]` *deflection factor* that scales the belt speed (flat ground
   passes unobstructed at factor 1).

Stored as unit direction (`wind_u`, `wind_v`) + `wind_magnitude` (speed).

### 4.4 Moisture / precipitation (`climate/moisture.py`)

Ocean-sourced moisture is advected downwind and rained out.

1. **Downwind fan (`build_downwind`).** For each cell, find the neighbors the
   wind pushes toward (positive alignment `dot(offset, wind)`) and weight them by
   that alignment, normalized. **Why a fan, not a single line:** single-file
   advection leaves most interior cells bone dry; a spreading front actually wets
   the land. Cells with no downwind neighbor are sinks (rain out in place).
2. **Rainout terms (computed once).** `base_rain` (steady drying) + `oro ×
   uphill` (orographic: air forced up downwind terrain rains harder) + `chill ×
   temperature drop`. These don't change between passes.
3. **Advection loop (`passes` iterations).** Each pass: refill ocean moisture
   (`evaporation × temperature`), rain out `moisture × rainout` into
   `precipitation`, and fan the remainder downwind. Accumulating over passes
   builds the steady-state pattern: wet windward coasts, dry rain-shadowed
   interiors.
4. **Saturating normalization.** *Changed in the recent fixes.* Raw rain-out is
   heavily right-skewed (a wet orographic minority, a long dry interior). The old
   percentile-and-clip scale piled the bulk on the arid floor (or, if lowered,
   the wet ceiling). Instead, normalize with a smooth saturating curve
   `p = raw / (raw + k)`, where `k` is the `wet_anchor_percentile` of land
   rain-out: the anchor maps to `0.5`, the dry interior stays dry, and the wet
   tail compresses smoothly toward `1` with **no pile-up at either end**.
   Anchoring to the median keeps each preset's character (a dry supercontinent
   stays dry; an ocean world stays wet).

---

## 5. Phase 3 — Water features

Re-route on the *final* (post-erosion, post-sea-level) terrain and extract the
named water features.

### 5.1 Discharge (`water/discharge.py`)

Re-run priority-flood + receivers on the final terrain, then accumulate flow
where each cell contributes its **precipitation** (not a flat 1.0 as in the
erosion drainage). One high→low sweep along the receiver tree. Ocean cells are
zeroed — discharge is a land quantity. This is the "how much water flows here"
field that defines rivers.

### 5.2 Rivers (`water/rivers.py`)

1. **Classify (`classify_rivers`).** A cell is a river if it is land, not a lake,
   and its discharge is in the top `river_fraction` of land discharge (a
   percentile threshold, so it self-adjusts to world size and wetness).
2. **Extract (`extract_rivers`).** Walk the receiver forest high→low. A river
   cell with no river inflow starts a new `River`; at a junction the
   largest-discharge inflow keeps the river identity and the others record
   `tributary_of`. A river ends (records its `mouth`) at ocean, a lake, or a
   non-river cell. Ties break by id for determinism.

### 5.3 Lakes (`water/lakes.py`, `stages/lakes.py`)

1. **Lake mask.** `is_land & (z_route > z + epsilon)` — terrain sitting below its
   own filled water surface is underwater, i.e. a lake.
2. **Components.** BFS connected components (the shared `components` helper).
3. **Outlets (`_find_outlet`).** A lake's outlet is its boundary cell whose
   outside neighbor has the lowest `z_route` — where the flood spilled in is
   where water spills out. If every outside neighbor is higher, the lake is
   terminal (endorheic, `outlet_cell = None`).
4. **Caldera injection — the one deliberate cross-stage coupling.** `LakesStage`
   reads `ctx.volcanoes` and stamps a single-cell terminal crater lake at each
   land caldera. A caldera is sub-grid at mesh resolution, so rather than hope
   erosion carves a bowl, the lake is injected directly.

### 5.4 Flow (`water/flow.py`)

Per-cell flow direction = unit vector from cell to receiver. Stylized speed =
`slope^0.3 × discharge^0.2`, normalized to `[0,1]` by the 95th percentile
(a Manning-flavored stylization, intentionally config-free). Lake-crossing
reaches are floored near-still. Non-river cells are zeroed.

---

## 6. Phase 4 — Magic & ecology

### 6.1 Savagery (`magic/savagery.py`)

Legible danger as a **weighted blend of named, normalized components** rather
than raw noise, so a place's danger is explainable:

- **remoteness** — coast distance, max-normalized (interiors are wild)
- **harshness** — climate distance from a comfort point (frozen/scorched = wild)
- **ruggedness** — slope, percentile-normalized (mountains are wild)
- **noise** — one FBm field (nature isn't a formula)
- **volcanism** — live volcanic ground is dangerous

Each is normalized to `[0,1]`, weighted, summed, and clipped.

### 6.2 Leylines (`magic/nexus.py`, `web.py`, `aspects.py`, `fields.py`)

The magic network is built in four steps:

1. **Nexus placement (`place_nexuses`).** Score every land cell (peaks, lake
   outlets, river confluences, volcanism, hot/cold ring alignment, + noise),
   then greedily accept the highest scorers subject to a minimum torus spacing.
   **Why score-then-space:** nexuses land on *significant* places without
   clumping.
2. **Web (`build_web`).** Connect the nexuses with a Kruskal **minimum spanning
   tree** over each nexus's `edge_k` nearest neighbors (the cheapest cycle-free
   network), then add back the shortest few rejected edges as **loops** (pure
   trees feel fragile). Edges are deterministic (sorted by length, then id).
3. **Aspects (`assign_aspects`).** Each nexus samples a **low-frequency** noise
   field for its valence (corrupt ↔ pure) — nearby nexuses sample similar
   values, so corruption clusters into coherent blighted regions for free —
   sharpened toward the poles by `purity`. Channel mix (corpus/mens/anima) is
   rolled and sharpened by `channel_purity`.
4. **Rasterize (`rasterize_magic`).** Every cell measures distance to the nearest
   leyline *segment* (point-to-segment, minimum-image). `magic_strength` =
   screen-combined line ridge + nexus peak over a low noise floor (screen-combine
   keeps it in `[0,1]` with no pile-up at the web). Valence/channels =
   inverse-distance blend over the nearest segments, faded toward neutral where
   magic is weak. Vectorized cells-per-segment (≈ n × segments, never n²).

### 6.3 Biomes (`ecology/biomes.py`, `stages/biomes.py`)

Biomes come from the one true `BIOME_GRID` (7 temperature bands × 7
precipitation bands = 49 biomes) in `core/model`.

1. **Centers (`derive_centers`).** Each biome's ideal climate point is its
   grid cell's midpoint `((t+0.5)/7, (p+0.5)/7)`. Deriving centers from the grid
   (instead of a separate table) keeps a single source of truth.
2. **Soft weights (`biome_weights`).** Inverse-distance weighting: each cell's
   membership in each biome is `1 / (distance_to_center + ε)^blend_sharpness`,
   normalized to a distribution. Negligible weights are dropped and the row
   renormalized. Ocean/lake cells are zeroed. The argmax of these weights equals
   the hard band grid cell — the continuous and discrete views agree.
3. **Spatial smoothing (`smooth_biome_weights`).** *Added in the recent fixes.* A
   hard argmax over per-cell weights speckles: where climate sits near a band
   boundary, cell-scale wiggle flips the dominant biome, so ~50% of biome
   "regions" end up a single tile. Diffuse the soft membership over **land
   neighbors** (a masked mesh-Laplacian, `smoothing_passes` × `smoothing_strength`;
   ocean/lake rows excluded so coasts don't bleed to zero), then renormalize.
   **Why:** biomes are regions with gradual ecotones, not salt-and-pepper. This
   cuts single-tile regions to ~10% while preserving nearly all biome variety.

---

## 7. Assembly — bake to grid (`bake/grid.py`, `bake/rivers.py`)

The mesh is finer than the gameplay grid, so the product is sampled down:

1. **Nearest cell per tile (`nearest_cell_per_tile`).** For each `size × size`
   tile center, find the nearest mesh cell with a periodic KD-tree.
2. **Bake (`bake_to_grid`).** Copy every product field (the `GridFields` subset)
   onto the grid by `field[nearest]` fancy indexing. Mesh-only intermediates
   (insolation, `z_route`, …) stay off the grid.
3. **Stamp rivers (`stamp_rivers`).** Rivers are 1-cell-wide paths that
   nearest-cell sampling would alias away, so they are rasterized onto the grid
   explicitly rather than left to the bake.

The result is a `WorldData` carrying the grid plus the feature lists (rivers,
lakes, landmasses, volcanoes, leyline network).

---

## 8. Appendix — recent root-cause fixes

For context, the changes that the sections above already fold in, and the bug
each addressed:

| Fix | Root cause | Where |
|---|---|---|
| Volcanoes materialized after finalize | discrete features built before the coastline existed → 100–180 submarine dots | §3.5, §3.8 |
| Continental freeboard | continental plates were flat slabs at sea level → land was the boundary skeleton (stringy) | §3.4 |
| Lapse from a lowland datum | sea-level lapse + high interiors → whole continents frozen | §4.2 |
| Temperate-biased insolation | raw cosine is U-shaped → starved temperate middle, ice-dominated | §4.1 |
| Saturating precipitation | percentile-and-clip stranded land on the arid floor → desert-dominated | §4.4 |
| Biome weight smoothing | hard argmax on noisy climate → salt-and-pepper biomes | §6.3 |

Each fix added or corrected a *process* (or, for the climate-distribution ones,
replaced a brittle remap with a principled, parameter-light one), rather than
patching a symptom downstream. A recurring theme: each fix exposed the next —
freeboard raised interiors, which revealed the lapse cold-bias, which (once
fixed) revealed the arid precipitation normalization. That chain is a sign they
were genuine root causes rather than surface tuning.
