# Phase 5 — Assembly: WorldData, Presets, Test Suite, Close-out

*Prerequisite: Phase 4. The shortest phase — no new algorithms. This is where
you act like the senior engineer: harden the contract, sweep the corners,
write down what you built.*

**What Phase 5 delivers:** the final `WorldData` handed to the (future)
persistence layer, presets in the new vocabulary, the consolidated invariant
suite, and an honest docs pass.

---

## Step 1 — The final `WorldData` (1–2 h)

Assemble the output contract exactly as the redesign plan §2 specifies:

```python
@dataclass
class WorldData:
    seed: int
    size: int
    config: WorldgenConfig        # resolved snapshot — reproducibility in one object
    grid: GridFields
    rivers: list[River]
    lakes: list[Lake]
    leylines: LeylineNetwork
    landmasses: list[Landmass]    # id, cell/tile count, class
```

Decisions to enforce while assembling:

- **The mesh does not ship.** `WorldgenPipeline.run(seed, size, config) ->
  WorldData` builds the mesh internally and lets it die. The viewer, which
  wants mesh intermediates, gets a second entry point (`run_debug` returning
  `(WorldData, WorldContext)`) — debug needs are real but they don't get to
  fatten the product type.
- **`region_id` ships as a column of `-1`s** in `GridFields` — the socket from
  planning, present so the persistence layer can schema it once.
- One conversion concern: feature objects refer to *mesh cells*. Decide their
  grid-facing form here — recommended: keep features in mesh coordinates
  (sites are world-space positions, valid over the grid too) and rely on the
  per-tile `river_id`/`lake_id` stamps for tile-side lookup. Resist inventing
  a tile-path representation nobody has asked for yet.

**Check:** a script builds a world end-to-end and prints a one-paragraph
census: land %, landmass count by class, river count (and longest), lake
count, nexus count, dominant-biome histogram top 5. Keep it — it's your
regression eyeball and your bragging artifact.

---

## Step 2 — Presets, rewritten in the new vocabulary (1–2 h)

The old presets tuned noise layers; the new ones tune *world physique*:

| Preset | Plate recipe | Sea | Character |
|---|---|---|---|
| `earthlike` | ~10 plates, ~0.45 continental | 0.32 land | balanced default |
| `pangaea` | fewer plates (~6), high continental fraction, low spacing → continental plates touch | 0.40+ | one supercontinent, big interior desert (watch the moisture map prove it) |
| `archipelago` | many plates (~16), low continental fraction, strong belt noise | 0.20 | island chains along boundaries |
| `wildlands` (new, optional) | any | any | savagery weights up, nexus count up, valence pushed corrupt — demonstrates the fantasy knobs are real knobs |

Each preset is a `WorldgenConfig` factory, ~10 lines. Generate and *look at*
each one; a preset that hasn't been looked at is a lie waiting for a user.

**Check:** census script over all presets × 3 seeds — no crashes, land
fractions near targets, qualitative character visible in the viewer.

---

## Step 3 — Consolidate the invariant suite (2–3 h)

You've accumulated tests phase by phase; now make the suite the contract's
enforcement arm. Structure `test/worldgen/` by subject and make sure every
clause of the plan's output contract has exactly one home:

- `test_determinism.py` — same seed twice → every array equal, every feature
  list equal. Parameterize over 2–3 seeds *and* 2 presets. (Still the most
  valuable file in the suite.)
- `test_geometry.py` — adjacency symmetry, neighbor count sanity, CSR
  well-formedness, torus wrap continuity of noise.
- `test_terrain.py` — elevation in [-1,1], sea at 0 (min<0<max), land
  fraction tolerance, downhill invariant, no NaN anywhere (cheap, catches
  everything numeric).
- `test_water.py` — discharge monotone along rivers, rivers terminate, lake
  outlets reach ocean, tile `river_id`s exist in `WorldData.rivers`.
- `test_climate_ecology.py` — field ranges, coast-wetter-than-interior,
  biome rows sum to 1, argmax-equals-`BIOME_GRID` agreement, magic ranges
  and channel rows sum to 1.

Two habits to bake in: every test takes `seed` as a parameter (a test that
passes for one seed tests one world); keep the whole suite under ~30 s
(`cell_count=500`, `size=40` fixtures — speed is what keeps a suite *run*).

**Check:** `uv run pytest test/worldgen -q` green; then mutate one constant
(flip an exponent sign in flow speed) and confirm something fails. A suite
that can't fail isn't testing.

---

## Step 4 — Performance pass (1–2 h, timeboxed)

Profile once, fix only what's slow, stop:

```bash
uv run python -m cProfile -s cumtime scripts/census.py | head -30
```

Expected profile at defaults (12k cells, 50 erosion iterations): erosion loop
dominates — that's *correct*, it's the real work. Worth fixing if they show
up: per-call overhead in `noise4` loops (batch with opensimplex's array API if
available), accidental O(n²) in leyline distance (should be n × segments),
pure-Python inner loops that have a numpy equivalent you skipped under
deadline. Not worth fixing: anything under a second.

Target: default world < ~10 s, census script says so at the end. If you're
within budget already, skip this step without guilt.

---

## Step 5 — Close-out (1–2 h)

- **Docs**: update `docs/worldgen-redesign-plan.md` — mark it *implemented*,
  note divergences (there will be some; the plan was a map, not a contract
  with yourself). Add a short `src/worldgen/README.md`: pipeline order, field
  glossary (name → meaning → range), how to run the viewer and census.
- **Sweep**: `grep -rn "MeshCell\|GridPositionData\|BiomeCenter\|LakeBasin\|biome_centers"`
  — zero hits in `src/`. Old config classes gone (`AnchorConfig`, the old
  savagery/alignment configs). `service/world.py` still broken — *expected*,
  out of scope, and now documented as such in its module docstring (one
  honest comment beats a mystery).
- **The known-broken note**: the next round (persistence) starts at
  `service/world.py` + `TileRepository` schema for the new fields. Write that
  sentence at the bottom of the plan doc so future-you starts warm.

## Exit criteria

- [ ] `WorldData` matches plan §2 exactly; mesh ephemeral; `region_id` socket present
- [ ] Presets rebuilt and visually verified
- [ ] Invariant suite consolidated, fast, and capable of failing
- [ ] Default world generates in seconds; census script tells the story
- [ ] Docs updated; old-world grep comes back empty

---

That's the whole rebuild. You'll have written: a graph data structure used by
real libraries, three flood-fills, a heap-ordered spatial algorithm published
in a hydrology journal, an implicit PDE solver, an advection simulation, an
MST with union-find, and a matrix-broadcast classifier — and you'll have a
world with rain shadows, river deltas, blighted regions, and a frostbelt to
show for it. The next conversation to have when you get here: persistence, or
regions (the clustering project we left a socket for). Bring screenshots.
