# Worldgen Guide — Code Conventions (House Style)

*Read this once, then keep it open while you work any phase. Every rule below is
extracted from the code already shipped in Phase 0 and Phase 1 (`src/worldgen/`).
The phase guides tell you **what** to build; this file tells you **exactly how to
write it** so your code is indistinguishable from what is already there. If a
phase guide and this file ever seem to disagree, this file wins on style.*

This file exists because the guides are followed by small models too. Small
models do best with **one obvious way to do each thing**. So everything here is a
hard rule, not a suggestion, unless it says "prefer".

---

## 0. The golden rule: copy the nearest existing file

Before writing a new module, open the closest Phase 0/1 file and mirror it:

| If you are writing… | Copy the shape of… |
|---|---|
| a pure algorithm (no `ctx`) | `src/worldgen/terrain/routing.py`, `terrain/erosion.py` |
| a `Stage` wrapper | `src/worldgen/stages/erosion.py`, `stages/finalize.py` |
| a config dataclass | `src/worldgen/config/worldgen_config.py` |
| a new field | `src/worldgen/fields.py` |
| a torus/vector helper | `src/worldgen/geometry/torus.py` |
| a test | `test/worldgen/test_plates.py`, `test_foundations.py` |

When in doubt, match the file you are editing, not this document.

---

## 1. Two layers, always: pure functions + thin stages

Every phase adds work in **two places**:

1. **Pure algorithm functions** in a domain package
   (`terrain/`, and new packages `climate/`, `water/`, `magic/`, `ecology/` as
   phases introduce them). These:
   - take `geometry`, plain numpy arrays, and a `cfg` dataclass — **never** the
     `WorldContext`.
   - are **keyword-only** (first parameter is `*`).
   - are **fully type-annotated** (params and return).
   - have a Google-style docstring (`Args:` / `Returns:`).
   - either return new arrays *or* mutate an array in place — and the docstring
     says which. (`stream_power_pass` mutates `z` in place; `priority_flood`
     returns a fresh `z_route`. Both are fine; be explicit.)

2. **`Stage` wrapper classes** in `stages/`. These:
   - implement the `Stage` protocol: `def run(self, ctx: WorldContext) -> None`.
   - read config via `ctx.config.<group>`.
   - validate prerequisites (see §6) and read inputs from `ctx.fields`.
   - build any `NoiseSource` via `ctx.noise_for("name")` and `FractalField`.
   - call the pure function(s).
   - assign results back onto `ctx.fields.*`.
   - contain **no algorithm logic** — just wiring. If a stage has a `for` loop
     doing math, it belongs in the pure layer.

This split is why Phase 1's functions are unit-testable without a pipeline. Keep
it.

---

## 2. File header and imports

Every file imports in three groups, blank-line separated, in this order:

```python
import heapq           # 1. stdlib
import random
from collections import deque
from dataclasses import dataclass

import numpy as np     # 2. third-party
from scipy.spatial import cKDTree

from src.worldgen.config.worldgen_config import ErosionConfig   # 3. local (always absolute, from src...)
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Float64Array, Int32Array
```

- Imports are **absolute** (`from src.worldgen...`), never relative.
- Ruff lint enforces `F401` (no unused imports) and `UP` (modern syntax). Don't
  leave dead imports. Run `uv run ruff check src/worldgen test/worldgen`.

---

## 3. Type annotations are mandatory and total

This codebase annotates **everything**, including local variables and loop
temporaries. This is the single most distinctive part of the house style.

```python
n: int = geometry.n_cells
collision: Float64Array = np.zeros(n, dtype=np.float64)

cell_id: int
for cell_id in range(n):
    plate_i: int = int(plate_id[cell_id])
    for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
        neighbor_id: int = int(neighbor_id)   # re-typed + converted from np scalar
        ...
```

Rules:

- Annotate every local with a meaningful type, including intermediates.
- When you pull a scalar out of a numpy array, convert and annotate:
  `z_i: float = float(z[cell_id])`, `r: int = int(receiver[cell_id])`.
- For numpy arrays, use the **type aliases** from `src/worldgen/types.py`:
  `Float64Array`, `Int32Array`, `Int8Array`, `BoolArray`, `IntPArray`. If you
  need a new one (e.g. a 2-D float array still uses `Float64Array`), add it to
  `types.py` rather than writing `NDArray[...]` inline.
- Declare a loop variable's type on its own line just above the loop when it
  helps readability (see `cell_id: int` above) — match what the surrounding
  file does.

---

## 4. Call style: prefer keyword arguments

Existing code calls almost everything by keyword, including numpy and scipy:

```python
np.zeros(shape=n, dtype=np.float64)
np.full(n, UNCLAIMED, dtype=np.int32)          # short positional like this also appears — match the file
np.argsort(a=z_route)
geometry.neighbors_of(cell_id=cell)
heapq.heappush(heap, (priority, neighbor_id, plate))
torus_distance(a=site_i, b=sites[r], width=geometry.width, height=geometry.height)
```

- Prefer keyword arguments for clarity, matching the function you are calling.
- Your **own** pure functions are keyword-only, so callers are forced into this
  anyway.

---

## 5. Errors: assign `msg`, then raise

Never raise with an inline string literal (ruff `EM101` style). Always:

```python
if n_plates < 1:
    msg: str = "n_plates must be at least 1"
    raise ValueError(msg)
```

Reuse the name `msg: str` for each raise site.

---

## 6. Stage prerequisite pattern (copy verbatim)

Stages depend on fields earlier stages wrote. `MeshFields` columns are typed
`X | None` (allocated lazily), so a stage must narrow `None` away before use.
This exact pattern is everywhere — reproduce it:

```python
plate_id_field: Int32Array | None = ctx.fields.plate_id
if plate_id_field is None:
    msg: str = "plate_id must be set before BoundaryUpliftStage"
    raise RuntimeError(msg)
plate_id: Int32Array = plate_id_field
```

For things stored on the context outside `fields` (like `plate_properties`),
same shape with `RuntimeError`.

---

## 7. Adding a field (one line in two places)

Per the Phase 0 payoff, a new per-cell field is **one line added to both**
`MeshFields` and `GridFields` in `src/worldgen/fields.py`, with `dtype` metadata:

```python
discharge: Float64Array | None = field(default=None, metadata={"dtype": np.float64})  # Water flow volume (rain-weighted)
```

- The trailing `#` comment states meaning and, where relevant, range.
- `allocate` and `bake_to_grid` pick it up automatically — do not touch them.
- A 2-D field (e.g. `magic_channels` shape `(n, 3)`) does **not** fit the generic
  1-D allocator. When a phase needs one, follow that phase's guide for how it is
  allocated/baked; do not silently break the generic path for the 1-D fields.

---

## 8. Adding a config (one dataclass + one registration)

In `src/worldgen/config/worldgen_config.py`, add a `@dataclass` under a banner
comment, one field per knob, **each with a default and an inline comment**:

```python
# ---------------------------------------------------------------------------
# Wind
# ---------------------------------------------------------------------------


@dataclass
class WindConfig:
    """Prevailing wind belts and terrain deflection."""

    belt_count: int = 3            # Number of zonal wind belts around the ring
    deflection: float = 0.5        # How hard wind bends away from uphill slopes
```

Then register it on `WorldgenConfig` with a `default_factory`:

```python
wind: WindConfig = field(default_factory=WindConfig)  # Prevailing wind + deflection
```

**Every magic number you write in an algorithm must come from a config field.**
No bare literals in the math except true mathematical constants (`2.0`, `0.5`
exponents that are part of the formula, `1e-8` epsilons).

---

## 9. Determinism (the invariant that catches the most bugs)

Phase 0's determinism test runs the **whole pipeline** and compares every array.
It will fail loudly if you break any of these:

- **Seeds** come from `ctx.seed_for("name")` (which is `subseed(seed, name)` via
  `crc32`). Never use Python's `hash()` (salted per process) and never thread one
  `Random` through multiple stages — give each purpose its own named sub-seed.
- **Heaps** must break ties deterministically. Push tuples whose **second element
  is the cell id**: `heapq.heappush(heap, (priority, cell_id, payload))`. Two
  equal priorities then order by id, not by object identity.
- **Order-dependent array passes** (diffusion, advection/moisture) must be
  **double-buffered**: read from the old array, write deltas/new values into a
  fresh array, apply/swap at the end. Never let cell `i` see cell `i-1`'s update
  within the same pass.
- **Set iteration**: if you build adjacency or candidates from a `set`, iterate
  it `sorted(...)` before writing into an ordered array (see
  `csr_from_lists`, which does `for neighbor_id in sorted(neighbors)`).
- `NoiseSource` is an **instance** (`opensimplex.OpenSimplex(seed)`); never call
  the module-level `opensimplex.seed()`.

---

## 10. Noise usage

- One `NoiseSource` per named purpose, from `ctx.noise_for("elevation")`. The name
  is the sub-seed key, so two differently-named sources are independent.
- Fractal/FBm noise uses `FractalField(sampler=..., field_id=FIELD_X, octaves=3)`.
- `field_id` is an integer constant declared at the top of
  `src/worldgen/noise/rng.py` (`FIELD_ELEVATION = 0`, `FIELD_BOUNDARY_UPLIFT = 1`,
  …). When a phase needs a new fractal field, **append a new `FIELD_*` constant**
  with the next integer; never reuse one for two purposes (the offset keeps fields
  decorrelated).
- To sample noise at every mesh site, follow the existing idiom
  (`_sample_site_noise` in `terrain/boundary_uplift.py`): build with `np.fromiter`
  over a generator of `field.sample(x=float(x), y=float(y), frequency=freq)`.

---

## 11. Torus math

- Any vector difference between two sites uses `torus_delta(a, b, width, height)`
  (minimum-image). Any distance uses `torus_distance(...)`. Both live in
  `src/worldgen/geometry/torus.py`. Do not hand-roll wrap arithmetic in a stage.
- Grid/tile coordinates wrap with `% size`; sites already live in
  `[0, width) × [0, height)`.
- These helpers operate on a **single pair** (1-D `(2,)` arrays). If a phase needs
  a vectorized batch version, add it to `torus.py` next to the existing ones with
  the same naming, fully typed.

---

## 12. CSR adjacency is your graph

- Neighbors of a cell: `geometry.neighbors_of(cell_id=i)` returns an `Int32Array`
  slice. Iterate it; convert each id with `int(...)`.
- Every graph traversal you write (BFS, multi-source BFS, connected components,
  priority-flood) loops over exactly these slices. There is **one** connected-
  components idiom in the codebase (the BFS in `terrain/finalize.py::label_landmasses`);
  reuse its shape. If a phase tells you to factor out a `components(geometry, mask)`
  helper, put it in the domain package that first needs it and import it elsewhere.

---

## 13. Pipeline registration

Each new stage is appended in order to `_build_stages()` in
`src/worldgen/pipeline.py`. Keep the list readable and in execution order. The
canonical order grows like this across phases:

```
Plates → PlatePersonality → BoundaryUplift → Erosion → Finalize
       → Insolation → Temperature → Wind → Moisture          (Phase 2)
       → Discharge → Rivers → Lakes → Flow                    (Phase 3)
       → Savagery → Leylines → Biomes                         (Phase 4)
```

(`Mesh` is built by the pipeline itself before stages run; it is not a `Stage`.)

---

## 14. Viewer layers

When a step says "add an `X` layer", edit `scripts/worldgen_render.py`:

1. add `X = "x"` to the `Layer` `StrEnum`,
2. add `Layer.X` to `LAYER_ORDER`,
3. add a label to `LAYER_LABELS`,
4. add a color branch in `rasterize_display` reading `grid.<field>`.

Layers read from `GridFields` arrays (baked), never from mesh objects.

---

## 15. Tests

- Live in `test/worldgen/`, one file per subject (Phase 5 consolidates them into
  `test_determinism.py`, `test_geometry.py`, `test_terrain.py`, `test_water.py`,
  `test_climate_ecology.py`).
- Use **small, fast fixtures**: `cell_count=500`, `size=40`–`50`. The whole suite
  stays under ~30 s.
- Pure functions are tested directly (see `test_plates.py`); whole-pipeline
  invariants go through `WorldgenPipeline(...).run(seed, size)`.
- **Every** phase re-asserts determinism. Prefer parameterizing tests over 2–3
  seeds with `@pytest.mark.parametrize` so a green test means more than one world.
- Docstring each test with the one-line invariant it defends.

---

## 16. Docstrings and comments

- Module docstring: one line stating the module's job (`"""Plate partition
  invariants: coverage, connectivity, determinism."""`). Do **not** leave
  `"""[TODO:description]"""` stubs — `terrain/boundary_uplift.py` has one; that is
  a wart to fix, not a pattern to copy.
- Pure functions: full Google-style docstring with `Args:`/`Returns:`.
- Stage `run` methods: one-line docstring of what it writes.
- In-function section banners use `# --- short label ---`.
- Comments explain **why**, not what the code already says.

---

## 17. Definition of done for any phase step

Before you mark a step complete:

- [ ] New fields added to **both** `MeshFields` and `GridFields`.
- [ ] New knobs added to a config dataclass and registered on `WorldgenConfig`.
- [ ] Pure function in the domain package, keyword-only, fully typed, docstringed.
- [ ] Thin `Stage` wrapper added and registered in `pipeline.py` in the right order.
- [ ] Viewer layer added if the step shows something.
- [ ] `uv run ruff check src/worldgen test/worldgen` clean.
- [ ] `uv run pytest test/worldgen -q` green, **including determinism**.
- [ ] The step's own "Check" passed (viewer eyeball or REPL/test assertion).
</content>

</invoke>
