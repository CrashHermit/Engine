# Phase 5 — Assembly: WorldData, Presets, Test Suite, Close-out

*Prerequisite: Phase 4. The shortest phase — no new algorithms. This is where
you act like the senior engineer: harden the contract, sweep the corners,
write down what you built.*

**What Phase 5 delivers:** the final `WorldData` handed to the (future)
persistence layer, presets in the new vocabulary, the consolidated invariant
suite, and an honest docs pass.

---

## Before you start (house style — read `CONVENTIONS.md`)

> **All code in this phase must match `docs/worldgen-guide/CONVENTIONS.md`.**
> No new algorithms — this phase is contract-hardening, so the style rules
> matter *more*, not less. `WorldData` is a plain `@dataclass` in
> `src/worldgen/features.py` (alongside `River`/`Lake`/`Landmass`/`LeylineNetwork`).

**Files you will touch:**

```
src/worldgen/features.py          # add @dataclass WorldData, Landmass (if missing)
src/worldgen/pipeline.py          # run() -> WorldData ; add run_debug() -> (WorldData, WorldContext)
src/worldgen/config/presets.py    # rewrite presets in the new vocabulary (+ optional wildlands)
scripts/census.py                 # NEW: one-paragraph world census (regression eyeball)
test/worldgen/                    # consolidate into the 5 subject files below
src/worldgen/README.md            # NEW: pipeline order + field glossary
docs/worldgen-redesign-plan.md    # mark implemented; note divergences
```

There is no new `Stage`, no new field, and no new config dataclass in this
phase. If you find yourself adding one, you are doing Phase 1–4 work that leaked.

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

### Implementation scaffold (house style)

`WorldData` in `features.py` — plain `@dataclass`, typed fields, matching the
existing dataclass style:

```python
@dataclass
class WorldData:
    seed: int
    size: int
    config: WorldgenConfig
    grid: GridFields
    rivers: list[River]
    lakes: list[Lake]
    leylines: LeylineNetwork
    landmasses: list[Landmass]
```

Pipeline entry points (`pipeline.py`):

```python
def run(self, seed: int, size: int) -> WorldData: ...
def run_debug(self, seed: int, size: int) -> tuple[WorldData, WorldContext]: ...
```

**Definition of done:** `run` builds the mesh internally and lets it die — the
mesh does **not** ship on `WorldData`; the viewer uses `run_debug` for mesh
intermediates. `GridFields` carries `region_id` as a column of `-1`s (the
persistence socket). Features stay in **mesh coordinates** (sites are world-space,
valid over the grid); tile-side lookup is the baked `river_id`/`lake_id`.

**Pitfalls:** resist inventing a tile-path river representation; resist fattening
`WorldData` with debug/mesh state. One product type, one debug door.

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

### Implementation scaffold (house style)

Extend the existing `config/presets.py` (it already has `earthlike`,
`archipelago`, `pangaea` as `WorldgenConfig` factories) in the **same shape** —
each preset is a function returning a `WorldgenConfig`, registered in the
`PRESETS` dict. Now that Phases 2–4 added configs, tune across groups:

```python
def wildlands() -> WorldgenConfig:
    """Demonstrate the fantasy knobs: savage, leyline-dense, corruption-leaning."""
    return WorldgenConfig(
        savagery=SavageryConfig(noise_weight=0.35, remoteness_weight=0.4),
        leyline=LeylineConfig(count=30),
        # valence pushed corrupt, etc.
    )
```

**Definition of done:** each preset is ~10 lines, registered in `PRESETS`, and has
been **looked at** in the viewer. Land fractions land near `target_land_fraction`.

**Pitfalls:** a preset never opened in the viewer is a lie — generate and eyeball
each one. Keep them factories (not module-level frozen instances baked at import)
if any preset needs per-call freshness.

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

### Implementation scaffold (house style)

Shared fixtures at the top of each file (or a `conftest.py`), matching
`test_foundations.py`:

```python
FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=500))
FAST_SIZE: int = 40
SEEDS: list[int] = [1, 7, 42]
```

The determinism test (the most valuable file) compares **every** array and
**every** feature list across two runs, parameterized over seeds and presets:

```python
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("preset", ["earthlike", "pangaea"])
def test_same_seed_same_world(seed: int, preset: str) -> None:
    """WorldgenPipeline is a pure function of (seed, size, config)."""
    a = WorldgenPipeline(PRESETS[preset]).run(seed=seed, size=FAST_SIZE)
    b = WorldgenPipeline(PRESETS[preset]).run(seed=seed, size=FAST_SIZE)
    # every GridFields array equal; rivers/lakes/leylines/landmasses equal
```

**Definition of done:** the five subject files exist (`test_determinism`,
`test_geometry`, `test_terrain`, `test_water`, `test_climate_ecology`); every
test takes `seed` as a parameter; suite runs under ~30 s; the deliberate-mutation
check actually turns something red.

**Note for this repo:** Phases 1–4 each specified invariant tests that may have
been verified by eye rather than committed (e.g. the Phase 1 downhill / land-
fraction / elevation-contract checks). Phase 5 is where those become permanent
pytests — audit each phase's "Check" lines and make sure every one has a home
here. A "Check" that never became a test is a regression waiting to happen.

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

### Implementation scaffold (house style)

`src/worldgen/README.md` — short, three sections:

1. **Pipeline order** — the `_build_stages()` list with a one-line job per stage.
2. **Field glossary** — a table: field name → meaning → range/dtype. Generate the
   rows straight from the `#` comments already on `MeshFields`/`GridFields` (that
   is why `CONVENTIONS.md` §7 requires them).
3. **How to run** — the viewer (`scripts/view_worldgen.py`) and census
   (`scripts/census.py`) commands.

The sweep is a literal command — run it and expect zero hits in `src/`:

```bash
uv run python -c "pass"  # sanity
grep -rn "MeshCell\|GridPositionData\|BiomeCenter\|LakeBasin\|biome_centers" src/
```

**Definition of done:** grep comes back empty in `src/`; `service/world.py` carries
a one-line module docstring saying it is known-broken and out of scope; the plan
doc is marked *implemented* with a divergences note.

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
