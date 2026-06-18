# Phase 4 — Magic & Ecology: Savagery, Leylines, Biomes

*Prerequisite: Phase 3. The most "yours" of all the phases — the algorithms
here generate fiction, not physics, so tuning taste matters more than
correctness. Also the phase where earlier investments pay out: every input
these stages need already exists.*

**What Phase 4 delivers:** terrain-derived savagery, the leyline/nexus network
with the valence × channel × strength magic fields, and biome soft weights
derived from the one true `BIOME_GRID`.

**Concepts you'll learn:** scoring + spacing for feature placement,
minimum spanning trees and union-find, point-to-segment distance, and
inverse-distance weighting (IDW) done with matrices.

New fields: `savagery`, `magic_strength`, `magic_valence` ([-1, 1]),
`magic_channels` (`(n, 3)`: corpus/mens/anima), `biome_weights`
(`(n, n_biomes)`). New configs: `SavageryConfig`, `LeylineConfig`,
`BiomeConfig`. New features in `WorldData`: `LeylineNetwork`.

---

## Before you start (house style — read `CONVENTIONS.md`)

> **All code in this phase must match `docs/worldgen-guide/CONVENTIONS.md`.**
> Pure functions in `src/worldgen/magic/` and `src/worldgen/ecology/`; thin
> `Stage` wrappers in `stages/`. This phase has **two 2-D fields**
> (`magic_channels` `(n, 3)`, `biome_weights` `(n, n_biomes)`) that do not fit
> the generic 1-D allocator — handle them per §"2-D fields" below.

**Files you will create:**

```
src/worldgen/magic/
    savagery.py        # pure: compute_savagery(...)
    nexus.py           # pure: place_nexuses(...)
    web.py             # pure: build_web(...)  (Kruskal + union-find + loops)
    aspects.py         # pure: assign_aspects(...)  (valence + channels)
    fields.py          # pure: rasterize_magic(...)  (strength/valence/channels)
src/worldgen/ecology/
    biomes.py          # pure: derive_centers(...), biome_weights(...)
src/worldgen/stages/
    savagery.py        # SavageryStage
    leylines.py        # LeylinesStage  (nexus + web + aspects + rasterize)
    biomes.py          # BiomeStage
src/worldgen/features.py   # add @dataclass LeylineNetwork
```

**1-D fields** (both `MeshFields` and `GridFields`):

```python
savagery: Float64Array | None = field(default=None, metadata={"dtype": np.float64})        # [0,1] danger/wildness
magic_strength: Float64Array | None = field(default=None, metadata={"dtype": np.float64})   # [0,1] leyline intensity
magic_valence: Float64Array | None = field(default=None, metadata={"dtype": np.float64})    # [-1,1] corrupt..pure
```

**2-D fields** (`magic_channels` `(n, 3)`, `biome_weights` `(n, n_biomes)`): the
generic `allocate`/`bake_to_grid` assume shape `(n,)`. Do **not** hack the generic
path. Instead allocate these explicitly in their stage
(`np.zeros((n, 3))`) and bake them with the same fancy-index trick the generic
bake uses but along axis 0: `grid_channels = mesh_channels[nearest]` (shape
`(size*size, 3)`). Add them as explicit columns the bake handles separately —
follow whatever Phase 5's `WorldData` assembly settles on, and leave a one-line
comment in `bake.py` pointing at the 2-D fields so the next reader knows.

**Configs:** `SavageryConfig` (component weights), `LeylineConfig` (nexus count,
spacing, edge `k`, loops, falloff reaches, purity exponents), `BiomeConfig`
(`blend_sharpness`, `weight_cutoff`). Register all three on `WorldgenConfig`.

**Noise constants** — append to `noise/rng.py`: `FIELD_SAVAGERY`,
`FIELD_NEXUS_SCORE`, `FIELD_VALENCE`, `FIELD_MAGIC_FLOOR`.

**External source of truth (do not re-declare):** biomes come from
`src/core/model/environment/ecology/biome.py`:
`BIOME_GRID: dict[tuple[TemperatureBand, PrecipitationBand], BiomeEnum]`, and the
band `BREAKPOINTS` in `core/model/environment/shared/temperature.py` /
`climate/precipitation.py`. Temperature/precip bands are **sevenths** (6
breakpoints → 7 bands; band `i` midpoint `(i + 0.5) / 7`). Phase 4 **derives**
biome centers from these; it must not reintroduce `config/biome_centers.py`
(deleted in Phase 0).

**Pipeline** — append in order: `SavageryStage(), LeylinesStage(), BiomeStage()`.

---

## Step 1 — Savagery from geography (1–2 h)

### The lesson first

Planning decision: savagery must be *legible* — players should be able to
reason "we're far from everything and it's frozen waste; stay alert." So it's
a weighted blend of named, normalized components, not raw noise:

- **remoteness** = `coast_distance`, normalized by its own max (interiors are
  wild).
- **harshness** = how far the cell's climate sits from comfortable —
  `dist((temperature, precipitation), (0.55, 0.5))`, normalized. Frozen
  wastes and scorched deserts are savage; mild wet lands are tame.
- **ruggedness** = `slope`, percentile-normalized (mountain country is wild).
- **noise** = one FBm field, because nature isn't a formula and surprises are
  content.

### What to build

`SavageryStage`: `savagery = clip(Σ wᵢ · componentᵢ, 0, 1)` with weights in
`SavageryConfig` (start `0.35 / 0.30 / 0.15 / 0.20`). Each component is an
array expression — the whole stage is ~15 lines and *zero* loops. (The
magic-coupling knob from the plan — corrupt zones breeding savagery — gets a
config slot at weight 0.0; wire it after step 5 if you want it.)

**Check (viewer):** `savagery` layer. Predict before looking: bright deep
interiors, bright deserts and frostbelt, bright ranges, calm temperate coasts.

### Implementation scaffold (house style)

`magic/savagery.py`:

```python
def compute_savagery(
    *,
    coast_distance: Float64Array,
    temperature: Float64Array,
    precipitation: Float64Array,
    slope: Float64Array,
    noise: Float64Array,
    cfg: SavageryConfig,
) -> Float64Array:
    """Weighted blend of remoteness, harshness, ruggedness, and noise; clipped to [0, 1]."""
```

`SavageryConfig`:

```python
@dataclass
class SavageryConfig:
    """Legible danger as a weighted blend of named geography components."""

    remoteness_weight: float = 0.35   # coast_distance, max-normalized
    harshness_weight: float = 0.30    # climate distance from comfort (0.55, 0.5)
    ruggedness_weight: float = 0.15   # slope, percentile-normalized
    noise_weight: float = 0.20        # FBm surprise
    magic_weight: float = 0.0         # corrupt zones breed savagery (wire after step 5)
```

**Definition of done:** every component **normalized** to `[0, 1]` before
weighting (remoteness by its max, ruggedness by percentile, harshness by its
max); whole stage is array math, **zero loops**; `np.clip(…, 0, 1)`.

**Pitfalls:** harshness is `dist((temperature, precipitation), (0.55, 0.5))` then
normalized — forgetting the normalize makes one component dominate. Weights are
config, not literals.

---

## Step 2 — Placing nexuses (2 h)

### The lesson first

Two requirements fight: nexuses should sit at *significant* places (drama),
but not bunch up (coverage). The standard pattern is **score + greedy
spacing**: score every candidate, take the best, ban its surroundings, repeat.
You've seen the spacing half before — the old `_place_anchors` did it with
random candidates; we upgrade random → scored.

### What to build

```python
def place_nexuses(geometry, fields, lakes, cfg, rng) -> list[int]   # cell ids
```

1. Score land cells: `score = z_peak_bonus + lake_outlet_bonus +
   confluence_bonus + ring_alignment_bonus + score_noise`. Peaks: top
   elevation percentile. Confluences: river cells with ≥ 2 river in-flows
   (computed in Phase 3, step 3 — keep it). Ring alignment: cells near the
   hot/cold ring lines (`|cos(phase)| ≈ 1`). Every bonus from config; noise
   keeps it from being deterministic-boring across worlds with similar
   terrain.
2. Greedy: sort by score, walk down, accept if `torus_distance` to every
   accepted nexus ≥ `cfg.min_spacing` (a fraction of world span), until
   `cfg.count` (~10–30) accepted.

**Check (viewer):** `leylines` layer, nexuses as bright dots. They should sit
on peaks, lake mouths, river forks — places that *mean* something.

### Implementation scaffold (house style)

`magic/nexus.py`:

```python
def place_nexuses(
    *,
    geometry: MeshGeometry,
    fields: MeshFields,
    lakes: list[Lake],
    cfg: LeylineConfig,
    rng: random.Random,
) -> list[int]:
    """Score every land cell, then greedily accept the best with torus-spacing >= min_spacing."""
```

**Definition of done:** scoring is array math (peak/lake-outlet/confluence/ring
bonuses + score noise); greedy spacing uses `torus_distance` against accepted
nexuses; `rng = random.Random(ctx.seed_for("leylines"))` from the stage (passed
in — pure function does not derive its own seed).

**Pitfalls:** `min_spacing` is a fraction of world span, not raw units; reuse the
confluence info from Phase 3 step 3 (river cells with ≥2 river inflows) rather
than recomputing; sort candidates by score **descending** and break ties by cell
id for determinism.

---

## Step 3 — The web: MST + loops (2–3 h)

### The lesson first

Connecting nexuses raises a classic problem: all pairwise connections is
spaghetti; too few disconnects the web. The **minimum spanning tree** is the
cheapest set of edges connecting everything — organic-looking, no cycles. Pure
trees feel fragile, though; ancient circuits should have redundancy, so we add
back a few short non-tree edges to create loops.

MST via **Kruskal's algorithm**, which is worth learning for its helper alone:
sort candidate edges by length, accept an edge iff its endpoints aren't
already connected. "Already connected" is answered by **union-find** — a
structure where each element points toward a representative; `find(x)` follows
pointers to the root, `union(a, b)` grafts one root onto the other. ~15 lines,
O(almost-1) per query, and it shows up across all of CS (it's also a slicker
way to do the connected-components passes you've written by BFS — once you
have it, you'll know both idioms).

### What to build

```python
@dataclass
class LeylineNetwork:
    nexus_cells: list[int]
    nexus_valence: np.ndarray      # step 4
    nexus_channels: np.ndarray     # (k, 3), step 4
    edges: list[tuple[int, int]]   # indices into nexus_cells
```

1. Candidate edges: each nexus to its `k` nearest fellow nexuses
   (torus distance, `k ≈ 4`), deduplicated.
2. Kruskal with union-find → MST.
3. Loops: from the rejected candidates, accept the `cfg.extra_loops` (~2–4)
   shortest.

**Check (viewer):** lines between nexus dots (a straight torus chord between
cell sites; remember minimum-image when it crosses the seam — draw two
partial segments). One connected web, a few loops, no spaghetti.

### Implementation scaffold (house style)

`magic/web.py`:

```python
def build_web(
    *,
    geometry: MeshGeometry,
    nexus_cells: list[int],
    cfg: LeylineConfig,
) -> list[tuple[int, int]]:
    """Kruskal MST over k-nearest nexus edges (torus distance) + a few shortest loop edges."""
```

Include a small union-find — keep it as module-level helpers in `web.py`:

```python
def _find(parent: list[int], x: int) -> int: ...
def _union(parent: list[int], rank: list[int], a: int, b: int) -> None: ...
```

`LeylineNetwork` (in `features.py`): `nexus_cells: list[int]`,
`nexus_valence: Float64Array`, `nexus_channels: Float64Array` (`(k, 3)`),
`edges: list[tuple[int, int]]` (indices into `nexus_cells`).

**Definition of done:** candidate edges = each nexus to its `cfg.edge_k` nearest
fellows (deduplicated, sorted by torus length); Kruskal accepts an edge iff
endpoints are in different sets; then accept the `cfg.extra_loops` shortest
rejected edges.

**Pitfalls:** edges store **indices into `nexus_cells`**, not cell ids; sort the
candidate list deterministically (length, then endpoint indices) so the MST is
reproducible.

---

## Step 4 — Aspects: clustered valence, mingling channels (1–2 h)

### The lesson first

Planning decision: corrupt nexuses cluster (coherent blighted regions with
contested borders), channel flavors mingle freely. Clustering sounds like it
needs an algorithm — neighbor propagation, voting — but there's a one-line
trick: **sample a low-frequency noise field at each nexus position**. Nearby
nexuses sample similar values (that's what low-frequency *means*), so valence
comes out spatially clustered with zero graph logic. Push values away from
the middle (`v = sign(v) * |v|^(1/cfg.purity)`) so most nexuses commit to a
side.

Channels: each nexus gets 3 random positive weights, normalized, sharpened by
an exponent (`w^cfg.channel_purity`, renormalize) — most nexuses lean one
channel without being pure.

**Check (REPL/viewer):** color nexus dots by valence (e.g. red↔blue). You
should *see* a corrupt cluster and a pure cluster, not salt-and-pepper.

### Implementation scaffold (house style)

`magic/aspects.py`:

```python
def assign_aspects(
    *,
    geometry: MeshGeometry,
    nexus_cells: list[int],
    cfg: LeylineConfig,
    valence_noise: FractalField,
    rng: random.Random,
) -> tuple[Float64Array, Float64Array]:
    """Return (nexus_valence (k,), nexus_channels (k, 3)): low-freq-sampled valence, sharpened channels."""
```

**Definition of done:** valence = `valence_noise.sample` at each nexus site (low
frequency → spatial clustering for free), then `v = sign(v) * |v|**(1/purity)`;
channels = 3 random positive weights per nexus, normalized, raised to
`channel_purity`, renormalized. `valence_noise` from `ctx.noise_for("valence")` /
`FIELD_VALENCE`.

**Pitfalls:** low frequency is what makes clustering emerge — a high-frequency
field gives salt-and-pepper. Sharpen valence toward the poles, not toward 0.

---

## Step 5 — Rasterizing magic fields (3–4 h)

### The lesson first

Every cell needs distance to the nearest leyline *segment* — point-to-segment
distance: project the point onto the segment's line, clamp the projection
parameter `t` to [0, 1], measure to that point:

```
t      = clamp(((p - a) · (b - a)) / |b - a|², 0, 1)
closest = a + t * (b - a)
```

On the torus, run it with minimum-image offsets relative to `a`. With ~30
nexuses → ~35 segments × 12k cells = ~400k evaluations — vectorize over cells
per segment (numpy broadcasting: all cells against one segment at a time, keep
a running minimum and argmin), or accept the loop; both are fine at this size.

Then the fields:

- `magic_strength = falloff(min_dist) + nexus_boost + floor_noise`, with
  `falloff = exp(-dist / cfg.line_reach)` and an extra, tighter exponential
  bump around nexus sites; `floor_noise` is a low FBm so "dead" zones still
  flicker. Clamp [0, 1].
- `magic_valence` / `magic_channels`: per cell, **IDW blend** over the `k`
  nearest segments — weight each segment by `1 / (dist + ε)`, blend its
  endpoint-interpolated aspect (lerp nexus aspects by the projection `t`),
  normalize. Far from the web (strength near floor), fade valence → 0 and
  channels → uniform ⅓ each: weak magic has no opinion.

**Check (viewer, the fun one):** three layers — `magic_strength` (glowing
web), `magic_valence` (diverging palette: corrupt color ↔ pure color),
`magic_channels` (map the 3 weights straight to RGB; it's a 3-composition,
RGB is a free visualization). The valence layer should show *regions*, the
channel layer mottled variety inside them.

### Implementation scaffold (house style)

`magic/fields.py`:

```python
def rasterize_magic(
    *,
    geometry: MeshGeometry,
    network: LeylineNetwork,
    cfg: LeylineConfig,
    floor_noise: FractalField,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Per-cell (magic_strength [0,1], magic_valence [-1,1], magic_channels (n, 3)) from segment distance + IDW."""
```

Add a torus-aware point-to-segment helper to `geometry/torus.py` (next to
`torus_delta`):

```python
def torus_point_segment(
    *, p: Float64Array, a: Float64Array, b: Float64Array, width: float, height: float
) -> tuple[float, float]:
    """Return (distance, t) from point p to segment a→b under minimum-image."""
```

**Definition of done:** clamp `t` to `[0, 1]`; vectorize cells-per-segment with a
running min/argmin (n × segments, **not** n²); `magic_strength =
exp(-dist/line_reach) + nexus_boost + floor_noise`, clipped; valence/channels are
IDW over the `k` nearest segments, faded to neutral (valence→0, channels→⅓ each)
where strength is near the floor.

**Pitfalls:** the `n²` trap — loop over **segments** (≈35), broadcasting all cells
against one segment at a time. Run minimum-image relative to `a`. `floor_noise`
from `ctx.noise_for("magic_floor")` / `FIELD_MAGIC_FLOOR`.

---

## Step 6 — Biomes from the one true grid (2–3 h)

### The lesson first

Planning decision: `BIOME_GRID` in `core/model` is the single source;
worldgen *derives* centers instead of hand-maintaining `biome_centers.py`.
Each biome occupies a band-cell — e.g. (MILD, HUMID) — and its "ideal point"
is that cell's midpoint, computed from the band `BREAKPOINTS` already in
`core/model` (bands are sevenths: band `i` spans `[i/7, (i+1)/7]`, midpoint
`(i + 0.5) / 7`).

Then **IDW soft weighting**, vectorized — this is the matrix thinking the
whole refactor has been training you for. With `T, P` shape `(n,)` and center
coordinates `ct, cp` shape `(49,)`, broadcasting gives every cell-to-center
distance at once:

```python
d2 = (T[:, None] - ct[None, :])**2 + (P[:, None] - cp[None, :])**2   # (n, 49)
w  = 1.0 / (np.sqrt(d2) + 1e-3) ** cfg.blend_sharpness
w *= dominance[None, :]                          # per-biome knob, all 1.0
w /= w.sum(axis=1, keepdims=True)                # rows sum to 1
w[w < cfg.weight_cutoff] = 0.0
w /= w.sum(axis=1, keepdims=True)                # renormalize after cutoff
```

`[:, None]` inserts an axis so `(n, 1)` against `(1, 49)` broadcasts to
`(n, 49)` — the line `T[:, None] - ct[None, :]` *is* the nested double loop
you'd have written, run in C. Ocean/lake cells: zero their rows.

### What to build

`derive_centers() -> (ct, cp, biome_order)` in the biome module (with the
biome order list — column index ↔ `BiomeEnum` mapping lives in exactly one
place), the IDW above as `BiomeStage`, and **delete `biome_centers.py`**.

**Check (viewer + test):** dominant-biome layer (argmax per row, one color per
biome — steal the old viewer's biome palette). Sanity: rainforest hugs the wet
hot zones, desert in rain shadows, tundra-equivalents along the frostbelt.
Test: every land row sums to 1; argmax biome equals
`BIOME_GRID[(temp_band, precip_band)]` for a sample of cells — the
"two views never disagree" guarantee, now enforced.

### Implementation scaffold (house style)

`ecology/biomes.py`:

```python
def derive_centers() -> tuple[Float64Array, Float64Array, list[BiomeEnum]]:
    """Return (center_temp (49,), center_precip (49,), biome_order): ideal points from BIOME_GRID band midpoints."""


def biome_weights(
    *,
    temperature: Float64Array,
    precipitation: Float64Array,
    is_land: BoolArray,
    center_temp: Float64Array,
    center_precip: Float64Array,
    cfg: BiomeConfig,
) -> Float64Array:
    """IDW soft weights over biome centers; shape (n, n_biomes); rows sum to 1 on land, 0 on water."""
```

**Definition of done:** `derive_centers` reads `BIOME_GRID` and the band
`BREAKPOINTS` from `core/model` — band `i` midpoint is `(i + 0.5) / 7`;
`biome_order` is the one place column index ↔ `BiomeEnum` is defined. The IDW is
the vectorized broadcast from the prose (`T[:, None] - ct[None, :]`), with
`weight_cutoff` + renormalize; ocean/lake rows zeroed.

**Pitfalls:** do **not** recreate `biome_centers.py`. Keep the `(n, 49)` matrix —
no per-cell Python loop. Land rows must sum to 1 *after* the cutoff renormalize.

### Test scaffold (house style)

```python
@pytest.mark.parametrize("seed", [1, 7, 42])
def test_biome_rows_sum_to_one_on_land(seed: int) -> None:
    """Every land cell's biome weights form a distribution."""

@pytest.mark.parametrize("seed", [1, 7, 42])
def test_argmax_biome_matches_grid(seed: int) -> None:
    """Dominant biome equals BIOME_GRID[(temp_band, precip_band)] — the 'two views agree' guarantee."""
```

## Exit criteria

- [ ] Savagery legible from geography in the viewer
- [ ] Leyline web: scored nexuses, MST + loops, clustered valence visible
- [ ] `magic_strength/valence/channels` fields baked to tiles
- [ ] Biomes derived from `BIOME_GRID`; `biome_centers.py` deleted; agreement
      test green
- [ ] Determinism still green (lots of rng entered this phase — check it)

**Phase 5** assembles the final `WorldData`, rebuilds the presets in the new
vocabulary, and closes out the test suite and docs.
