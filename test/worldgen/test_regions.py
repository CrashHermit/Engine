"""Regions socket: every tile is assigned, ids are a clean contract, deterministic."""

import numpy as np
import pytest

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.features import RegionKind, WorldData
from src.worldgen.pipeline import WorldgenPipeline

SEEDS: tuple[int, ...] = (0, 7, 42)
FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=500))

_GEOGRAPHIC_KINDS: frozenset[RegionKind] = frozenset(
    {RegionKind.LANDMASS, RegionKind.OCEAN}
)
_BIOME_KINDS: frozenset[RegionKind] = frozenset(
    {
        RegionKind.FOREST,
        RegionKind.GRASSLAND,
        RegionKind.DESERT,
        RegionKind.TUNDRA,
        RegionKind.WETLAND,
        RegionKind.SHRUBLAND,
    }
)


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
    """Region ids are 0-based, contiguous, and every region surfaces on a column."""
    world = _world(seed)
    ids = sorted(r.id for r in world.regions)
    assert ids == list(range(len(world.regions)))

    # Regions are layered across two columns; their union must cover every id with
    # no strays (geographic ids live in region_id, biome-region ids in the other).
    on_grid = (
        set(np.unique(world.grid.region_id).tolist())
        | set(np.unique(world.grid.biome_region_id).tolist())
    )
    on_grid.discard(-1)
    assert on_grid == {r.id for r in world.regions}


@pytest.mark.parametrize("seed", SEEDS)
def test_region_kinds_and_landmass_agreement(seed: int) -> None:
    """Kinds are the supported set, and land regions match the landmasses."""
    world = _world(seed)
    kinds = {r.kind for r in world.regions}
    assert kinds <= _GEOGRAPHIC_KINDS | _BIOME_KINDS

    land_regions = [r for r in world.regions if r.kind == RegionKind.LANDMASS]
    assert len(land_regions) == len(world.landmasses)
    # At least one ocean body exists in a partial-land world.
    assert any(r.kind == RegionKind.OCEAN for r in world.regions)


@pytest.mark.parametrize("seed", SEEDS)
def test_biome_regions_overlap_land_and_carry_a_biome(seed: int) -> None:
    """Biome-regions cover dry land, are a separate layer, and name their biome."""
    world = _world(seed)
    brid = world.grid.biome_region_id
    assert brid is not None

    biome_regions = [r for r in world.regions if r.kind in _BIOME_KINDS]
    assert biome_regions  # a partial-land world has at least one biome-region
    # Every biome-region carries its dominant biome; geographic bodies do not.
    assert all(r.dominant_biome is not None for r in biome_regions)
    assert all(
        r.dominant_biome is None
        for r in world.regions
        if r.kind in {RegionKind.LANDMASS, RegionKind.OCEAN}
    )

    # The biome layer overlaps — not equals — the geographic partition: every
    # tile with a biome-region also has a (land) geographic region, but ocean
    # tiles have a region and no biome-region.
    has_biome = brid >= 0
    assert bool((world.grid.region_id[has_biome] >= 0).all())
    assert int((brid < 0).sum()) > 0  # ocean/lake tiles carry no biome-region


@pytest.mark.parametrize("seed", SEEDS)
def test_biome_region_ids_index_into_the_shared_list(seed: int) -> None:
    """Both id columns index the single global ``regions`` list (one id space)."""
    world = _world(seed)
    n_regions = len(world.regions)
    for column in (world.grid.region_id, world.grid.biome_region_id):
        present = np.unique(column[column >= 0])
        assert present.size == 0 or int(present.max()) < n_regions


@pytest.mark.parametrize("seed", SEEDS)
def test_regions_are_deterministic(seed: int) -> None:
    """Same seed → identical region ids, kinds, and names (stable gameplay handles)."""
    a = _world(seed)
    b = _world(seed)
    assert [(r.id, r.kind, r.name, r.dominant_biome) for r in a.regions] == [
        (r.id, r.kind, r.name, r.dominant_biome) for r in b.regions
    ]
    assert np.array_equal(a.grid.region_id, b.grid.region_id)
    assert np.array_equal(a.grid.biome_region_id, b.grid.biome_region_id)
