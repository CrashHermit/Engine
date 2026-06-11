Steps 0–4 look done: `build_mesh` is in `mesh.py`, and `rng.py` has `subseed`, `NoiseSource`, and `sample_array`. **Step 5** is context + pipeline shell + placeholder elevation.

---

## Step 5 goal

Wire the new pieces into a runnable pipeline:

1. **`WorldContext`** — `config`, `geometry`, `fields` (not `WorldData`)
2. **`Stage` protocol** — `run(ctx) -> None`, mutate `ctx.fields` in place
3. **`PlaceholderElevationStage`** — FBm noise → normalized elevation → `is_land`
4. **`WorldgenPipeline`** (new shell) — build mesh, allocate fields, run stages

Keep the old `context.py` / `pipeline.py` / `stages/*` on disk until Step 9. For Step 5 you can either **overwrite** those two files (old pipeline breaks until Step 7 viewer update) or add parallel modules like `context_new.py` — overwriting is fine if you only test via a small script for now.

---

## 1. New `WorldContext`

Replace the old dataclass (which held `data`, `sampler`, `rng`) with:

```python
from __future__ import annotations

from dataclasses import dataclass, replace

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.fields import MeshFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.rng import NoiseSource, subseed


@dataclass
class WorldContext:
    """Shared state for the worldgen pipeline."""

    config: WorldgenConfig
    geometry: MeshGeometry
    fields: MeshFields

    def seed_for(self, name: str) -> int:
        """Deterministic sub-seed for a named stage or purpose."""
        return subseed(self.config.seed, name)

    def noise_for(self, name: str) -> NoiseSource:
        """NoiseSource scoped to this world's torus and sub-seed."""
        width = self.geometry.width
        height = self.geometry.height
        return NoiseSource(self.seed_for(name), width, height)

    @staticmethod
    def resolve_config(
        seed: int,
        size: int,
        config: WorldgenConfig | None = None,
    ) -> WorldgenConfig:
        """Apply seed/size and resolve mesh width/height from config."""
        cfg = config or WorldgenConfig()
        mesh_width = cfg.mesh.width or float(size)
        mesh_height = cfg.mesh.height or float(size)
        resolved_mesh = replace(cfg.mesh, width=mesh_width, height=mesh_height)
        return replace(cfg, seed=seed, size=size, mesh=resolved_mesh)
```

`noise_for("elevation")` uses `subseed` so adding stages later won't reshuffle unrelated RNG.

---

## 2. Stage protocol

Put this in a small new file (e.g. `stage.py`) so you don't have to touch old `stages/base.py` yet:

```python
from __future__ import annotations

from typing import Protocol

from src.worldgen.context import WorldContext


class Stage(Protocol):
    """Pipeline stage that mutates ctx.fields in place."""

    def run(self, ctx: WorldContext) -> None:
        """Execute the stage."""
        ...
```

Old protocol returned `WorldContext`; new one returns `None` — less ceremony.

---

## 3. `PlaceholderElevationStage`

New file, e.g. `stages/placeholder_elevation.py`:

```python
from __future__ import annotations

import numpy as np

from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.sampler import FIELD_LAYER_BASE


class PlaceholderElevationStage:
    """Temporary noise elevation until Phase 1 terrain replaces it."""

    def run(self, ctx: WorldContext) -> None:
        span = min(ctx.geometry.width, ctx.geometry.height)
        frequency = 4.0 / span

        field = FractalField(
            ctx.noise_for("elevation"),
            field_id=FIELD_LAYER_BASE,
            octaves=3,
        )

        xs = ctx.geometry.sites[:, 0]
        ys = ctx.geometry.sites[:, 1]
        z = np.fromiter(
            (field.sample(float(x), float(y), frequency) for x, y in zip(xs, ys)),
            dtype=np.float64,
            count=ctx.geometry.n_cells,
        )

        z_min = z.min()
        z_max = z.max()
        ctx.fields.elevation = (z - z_min) / (z_max - z_min)
        ctx.fields.is_land = ctx.fields.elevation > 0.6
```

The SoA win is the last two lines — whole-array assign, no per-cell objects.

`frequency = 4.0 / span` is arbitrary but reasonable; tune later in the viewer.

---

## 4. New pipeline shell

Replace `pipeline.py` with something minimal:

```python
from __future__ import annotations

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.fields import MeshFields
from src.worldgen.geometry.mesh import build_mesh
from src.worldgen.stage import Stage
from src.worldgen.stages.placeholder_elevation import PlaceholderElevationStage


def _build_stages() -> list[Stage]:
    return [
        PlaceholderElevationStage(),
    ]


class WorldgenPipeline:
    """Phase 0 pipeline: mesh + placeholder elevation."""

    def __init__(self, config: WorldgenConfig | None = None) -> None:
        self._config = config

    def run(self, seed: int, size: int) -> WorldContext:
        cfg = WorldContext.resolve_config(seed, size, self._config)
        mesh_cfg = cfg.mesh

        geometry = build_mesh(
            seed=cfg.seed,
            cell_count=mesh_cfg.cell_count,
            lloyd_iterations=mesh_cfg.lloyd_iterations,
            width=mesh_cfg.width,
            height=mesh_cfg.height,
        )
        fields = MeshFields.allocate(geometry.n_cells)
        ctx = WorldContext(config=cfg, geometry=geometry, fields=fields)

        for stage in _build_stages():
            stage.run(ctx)

        return ctx
```

Mesh build lives in `run()`, not a stage — geometry exists before any stage runs.

---

## 5. Exit check (5-line script)

```python
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.config.worldgen_config import WorldgenConfig, MeshConfig

ctx = WorldgenPipeline(
    WorldgenConfig(mesh=MeshConfig(cell_count=2000))
).run(seed=42, size=100)

print(ctx.fields.elevation.min(), ctx.fields.elevation.max(), ctx.fields.is_land.mean())
```

Expect:
- `min` ≈ `0.0`, `max` ≈ `1.0`
- `is_land.mean()` somewhere in `(0, 1)` — not 0 or 1
- Runs in well under a second

---

## File map for Step 5

| File | Action |
|------|--------|
| `context.py` | Replace with new `WorldContext` |
| `stage.py` | New — `Stage` protocol |
| `stages/placeholder_elevation.py` | New — placeholder stage |
| `pipeline.py` | Replace with new shell |
| `stages/base.py`, old stages | Leave alone until Step 9 |
| `data.py` | Don't touch yet |

---

## Pitfalls

| Issue | Fix |
|-------|-----|
| `FractalField` needs a sampler with `.sample(x,y,freq,offset)` | Pass `ctx.noise_for("elevation")` — already compatible |
| Division by zero if all noise identical | Extremely unlikely; add `if z_max > z_min` guard if paranoid |
| Old imports break (`WorldContext.build`, `ctx.data`) | Expected until Step 7 viewer + Step 9 cleanup |
| `FIELD_LAYER_BASE` in old `sampler.py` | Fine to import for now; move constant to `rng.py` later |

---

## After Step 5

| Step | What |
|------|------|
| **6** | `bake.py` — `nearest_cell_per_tile`, `GridFields`, generic mesh→grid gather |
| **7** | Port viewer to new pipeline + `GridFields` |
| **8** | `test/worldgen/test_foundations.py` — determinism, adjacency, wrap |

Step 4 is already in good shape — run the wrap check if you haven't:

```python
from src.worldgen.noise.rng import NoiseSource
n = NoiseSource(42, 100.0, 100.0)
assert n.sample(0, 0, 4.0) == n.sample(100.0, 0, 4.0)
assert n.sample(0, 0, 4.0) == n.sample(0, 100.0, 4.0)
```

Paste your `context.py` / `pipeline.py` when written if you want a review before Step 6.