"""Regions socket: every tile is assigned, ids are a clean contract, deterministic."""

import numpy as np
import pytest

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.features import RegionKind, WorldData
from src.worldgen.pipeline import WorldgenPipeline

SEEDS: tuple[int, ...] = (0, 7, 42)
FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=500))


def _world(seed: int) -> WorldData:
    return WorldgenPipeline(FAST_CONFIG).run(seed=seed, size=48)


@pytest.mark.parametrize("seed", SEEDS)
def test_region_partition_is_complete(seed: int) -> None:
    """Every tile gets a region: the baked ``region_id`` has no ``-1`` holes."""
    world = _world(seed)
    assert world.grid.region_id is not None
    assert int(world.grid.region_id.min()) >= 0


@pytest.mark.parametrize("seed", SEEDS)
def test_region_ids_are_a_contiguous_contract(seed: int) -> None:
    """Region ids are 0-based and contiguous, and every region appears on the grid."""
    world = _world(seed)
    ids = sorted(r.id for r in world.regions)
    assert ids == list(range(len(world.regions)))

    on_grid = set(np.unique(world.grid.region_id).tolist())
    assert on_grid <= {r.id for r in world.regions}
    # Every region with cells must surface on at least one tile (no orphans).
    assert on_grid == {r.id for r in world.regions}


@pytest.mark.parametrize("seed", SEEDS)
def test_region_kinds_and_landmass_agreement(seed: int) -> None:
    """Only the geography-stable kinds ship, and land regions match landmasses."""
    world = _world(seed)
    kinds = {r.kind for r in world.regions}
    assert kinds <= {RegionKind.LANDMASS, RegionKind.OCEAN}

    land_regions = [r for r in world.regions if r.kind == RegionKind.LANDMASS]
    assert len(land_regions) == len(world.landmasses)
    # At least one ocean body exists in a partial-land world.
    assert any(r.kind == RegionKind.OCEAN for r in world.regions)


@pytest.mark.parametrize("seed", SEEDS)
def test_regions_are_deterministic(seed: int) -> None:
    """Same seed → identical region ids, kinds, and names (stable gameplay handles)."""
    a = _world(seed)
    b = _world(seed)
    assert [(r.id, r.kind, r.name) for r in a.regions] == [
        (r.id, r.kind, r.name) for r in b.regions
    ]
    assert np.array_equal(a.grid.region_id, b.grid.region_id)
