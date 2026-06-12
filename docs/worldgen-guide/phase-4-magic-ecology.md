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

## Exit criteria

- [ ] Savagery legible from geography in the viewer
- [ ] Leyline web: scored nexuses, MST + loops, clustered valence visible
- [ ] `magic_strength/valence/channels` fields baked to tiles
- [ ] Biomes derived from `BIOME_GRID`; `biome_centers.py` deleted; agreement
      test green
- [ ] Determinism still green (lots of rng entered this phase — check it)

**Phase 5** assembles the final `WorldData`, rebuilds the presets in the new
vocabulary, and closes out the test suite and docs.
