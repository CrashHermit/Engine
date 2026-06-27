"""Vulcanism invariants: field range, the collision gate, chains, consistency."""

from collections import defaultdict

import numpy as np
import pytest

from src.worldgen.bake.grid import nearest_cell_per_tile
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.core.model.environment.terrain.volcano import VolcanoKind
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.terrain.boundaries import BoundaryKind

FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=1500))
FAST_SIZE: int = 40
SEEDS: list[int] = [1, 7, 42]

_CACHE: dict[int, tuple] = {}


def _debug(seed: int):
    if seed not in _CACHE:
        _CACHE[seed] = WorldgenPipeline(FAST_CONFIG).run_debug(seed=seed, size=FAST_SIZE)
    return _CACHE[seed]


@pytest.mark.parametrize("seed", SEEDS)
def test_volcanism_field_in_unit_range(seed: int) -> None:
    """The volcanism field stays in [0, 1]."""
    _w, ctx = _debug(seed)
    v = ctx.fields.volcanism
    assert v is not None
    assert float(v.min()) >= 0.0
    assert float(v.max()) <= 1.0 + 1e-9


@pytest.mark.parametrize("seed", SEEDS)
def test_at_least_some_volcanoes(seed: int) -> None:
    """A plate world produces volcanoes (arcs, hotspots, or ridges)."""
    world, _ctx = _debug(seed)
    assert len(world.volcanoes) > 0


@pytest.mark.parametrize("seed", SEEDS)
def test_no_arc_volcano_on_collision(seed: int) -> None:
    """The Himalaya gate: no stratovolcano sits on a continent-continent cell."""
    world, ctx = _debug(seed)
    cc = ctx.boundary_facts.conv_kind == int(BoundaryKind.CONV_CC)
    for v in world.volcanoes:
        if v.kind is VolcanoKind.STRATO:
            assert not cc[v.cell], f"arc volcano on a collision cell {v.cell}"


@pytest.mark.parametrize("seed", SEEDS)
def test_volcano_columns_consistent(seed: int) -> None:
    """is_volcano <=> volcano_id >= 0, and each id points back to its summit cell."""
    world, ctx = _debug(seed)
    is_volcano = ctx.fields.is_volcano
    volcano_id = ctx.fields.volcano_id
    np.testing.assert_array_equal(is_volcano, volcano_id >= 0)
    for v in world.volcanoes:
        assert is_volcano[v.cell]
        assert int(volcano_id[v.cell]) == v.id


@pytest.mark.parametrize("seed", SEEDS)
def test_hotspot_trails_decay(seed: int) -> None:
    """Within a hotspot (shield) chain, activity is non-increasing down the trail.

    Volcanoes are appended in trail order, so ascending id within a chain_id is
    trail order; activity must not rise along it (active head, subsiding tail).
    """
    world, _ctx = _debug(seed)
    by_chain: dict[int, list] = defaultdict(list)
    for v in world.volcanoes:
        if v.kind is VolcanoKind.SHIELD and v.chain_id >= 0:
            by_chain[v.chain_id].append(v)
    checked = 0
    for chain in by_chain.values():
        chain.sort(key=lambda v: v.id)
        activities = [v.activity for v in chain]
        assert activities == sorted(activities, reverse=True), (
            f"hotspot chain activity not monotonic: {activities}"
        )
        checked += len(chain)
    assert checked > 0, "expected at least one hotspot shield"


@pytest.mark.parametrize("seed", SEEDS)
def test_land_calderas_hold_water(seed: int) -> None:
    """Every caldera volcano on land has water at its summit.

    Usually that is a freshly injected single-cell terminal crater lake; if the
    summit already sits inside a natural lake, the caldera simply shares it.
    """
    world, ctx = _debug(seed)
    is_land = ctx.fields.is_land
    is_lake = ctx.fields.is_lake
    lake_by_id = {lk.id: lk for lk in world.lakes}
    injected = 0
    for v in world.volcanoes:
        if v.has_caldera and is_land[v.cell]:
            assert is_lake[v.cell], f"land caldera {v.cell} holds no water"
            lake = lake_by_id[int(ctx.fields.lake_id[v.cell])]
            if lake.cells == [v.cell]:  # our injected crater lake
                assert lake.outlet_cell is None  # crater lakes are terminal
                injected += 1
    assert injected > 0, "expected at least one injected crater lake"


@pytest.mark.parametrize("seed", SEEDS)
def test_bake_parity(seed: int) -> None:
    """Grid volcanism is the nearest-cell gather of the mesh field."""
    world, ctx = _debug(seed)
    nearest = nearest_cell_per_tile(ctx.geometry, FAST_SIZE)
    np.testing.assert_array_equal(world.grid.volcanism, ctx.fields.volcanism[nearest])
    np.testing.assert_array_equal(world.grid.volcano_id, ctx.fields.volcano_id[nearest])
