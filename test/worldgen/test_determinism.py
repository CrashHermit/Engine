"""Determinism: WorldgenPipeline is a pure function of (seed, size, config).

The most valuable file in the suite — it compares **every** grid array and
**every** feature list across two runs, over multiple seeds and presets.
"""

from dataclasses import fields as dataclass_fields
from dataclasses import replace

import numpy as np
import pytest

from src.worldgen.config.presets import PRESETS
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.features import LeylineNetwork, River, WorldData
from src.worldgen.fields import GridFields
from src.worldgen.pipeline import WorldgenPipeline

FAST_SIZE: int = 40
SEEDS: list[int] = [1, 7, 42]
PRESET_NAMES: list[str] = ["earthlike", "pangaea"]


def _fast(preset: str) -> WorldgenConfig:
    """A preset shrunk to the fast test mesh."""
    return replace(PRESETS[preset], mesh=MeshConfig(cell_count=500))


def _assert_grids_equal(a: GridFields, b: GridFields) -> None:
    for f in dataclass_fields(a):
        va = getattr(a, f.name)
        vb = getattr(b, f.name)
        assert np.array_equal(va, vb), f"grid.{f.name} differs"


def _assert_rivers_equal(a: list[River], b: list[River]) -> None:
    assert len(a) == len(b), "river count differs"
    for ra, rb in zip(a, b):
        assert ra.id == rb.id
        assert ra.cells == rb.cells
        assert ra.mouth == rb.mouth
        assert ra.tributary_of == rb.tributary_of
        assert np.array_equal(ra.discharge, rb.discharge)


def _assert_leylines_equal(a: LeylineNetwork, b: LeylineNetwork) -> None:
    assert a.nexus_cells == b.nexus_cells
    assert a.edges == b.edges
    assert np.array_equal(a.nexus_valence, b.nexus_valence)
    assert np.array_equal(a.nexus_channels, b.nexus_channels)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("preset", PRESET_NAMES)
def test_same_seed_same_world(seed: int, preset: str) -> None:
    """Two runs of the same (seed, size, config) produce an identical WorldData."""
    cfg: WorldgenConfig = _fast(preset)
    a: WorldData = WorldgenPipeline(cfg).run(seed=seed, size=FAST_SIZE)
    b: WorldData = WorldgenPipeline(cfg).run(seed=seed, size=FAST_SIZE)

    assert a.seed == b.seed and a.size == b.size
    _assert_grids_equal(a.grid, b.grid)
    _assert_rivers_equal(a.rivers, b.rivers)
    assert a.lakes == b.lakes  # plain dataclasses (no arrays)
    assert a.landmasses == b.landmasses
    _assert_leylines_equal(a.leylines, b.leylines)


@pytest.mark.parametrize("seed", SEEDS)
def test_run_matches_run_debug(seed: int) -> None:
    """run() returns exactly the WorldData that run_debug() does."""
    cfg: WorldgenConfig = _fast("earthlike")
    world_only: WorldData = WorldgenPipeline(cfg).run(seed=seed, size=FAST_SIZE)
    world_debug, _ctx = WorldgenPipeline(cfg).run_debug(seed=seed, size=FAST_SIZE)
    _assert_grids_equal(world_only.grid, world_debug.grid)
    _assert_rivers_equal(world_only.rivers, world_debug.rivers)
