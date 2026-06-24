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
from src.worldgen.features import Nexus, River, Vein, WorldData
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


def _assert_veins_equal(a: list[Vein], b: list[Vein]) -> None:
    assert len(a) == len(b), "vein count differs"
    for va, vb in zip(a, b):
        assert va.id == vb.id
        assert va.cells == vb.cells
        assert va.source_nexus == vb.source_nexus
        assert va.mouth_nexus == vb.mouth_nexus
        assert va.tributary_of == vb.tributary_of
        assert np.array_equal(va.strength, vb.strength)
        assert np.array_equal(va.channels, vb.channels)


def _assert_nexuses_equal(a: list[Nexus], b: list[Nexus]) -> None:
    assert len(a) == len(b), "nexus count differs"
    for na, nb in zip(a, b):
        assert na.id == nb.id
        assert na.cell == nb.cell
        assert na.polarity == nb.polarity
        assert na.charge == nb.charge
        assert np.array_equal(na.channels, nb.channels)


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
    _assert_veins_equal(a.veins, b.veins)
    _assert_nexuses_equal(a.nexuses, b.nexuses)
    assert a.volcanoes == b.volcanoes  # plain dataclasses (no arrays)


@pytest.mark.parametrize("seed", SEEDS)
def test_run_matches_run_debug(seed: int) -> None:
    """run() returns exactly the WorldData that run_debug() does."""
    cfg: WorldgenConfig = _fast("earthlike")
    world_only: WorldData = WorldgenPipeline(cfg).run(seed=seed, size=FAST_SIZE)
    world_debug, _ctx = WorldgenPipeline(cfg).run_debug(seed=seed, size=FAST_SIZE)
    _assert_grids_equal(world_only.grid, world_debug.grid)
    _assert_rivers_equal(world_only.rivers, world_debug.rivers)
