"""Phase 3 water invariants: discharge monotone, river continuity, determinism.

These tests exercise the river extraction pipeline:
- ``classify_rivers`` (step 2): percentile threshold
- ``extract_rivers`` (step 3): downstream-first River objects
"""

import numpy as np
import pytest

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline

SEEDS = [1, 7, 42]
FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=500))
FAST_SIZE = 40


def _run(ctx_seed: int) -> tuple:
    """Run the pipeline (debug door) and return (ctx, rivers, receiver, ...)."""
    _world, ctx = WorldgenPipeline(FAST_CONFIG).run_debug(
        seed=ctx_seed, size=FAST_SIZE
    )
    return (
        ctx,
        ctx.rivers,
        ctx.fields.receiver,
        ctx.fields.discharge,
        ctx.fields.is_river,
        ctx.fields.river_id,
    )


# ---------------------------------------------------------------------------
# Step 3 — River continuity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_river_cells_contiguous(seed: int) -> None:
    """Every river's cells are contiguous: receiver[cells[k]] == cells[k+1]."""
    ctx, rivers, receiver, discharge, is_river, river_id = _run(seed)

    for river in rivers:
        cells = river.cells
        for k in range(len(cells) - 1):
            assert receiver[cells[k]] == cells[k + 1], (
                f"river {river.id} break at k={k}: "
                f"receiver[{cells[k]}]={receiver[cells[k]]} != {cells[k + 1]}"
            )


# ---------------------------------------------------------------------------
# Step 3 — Discharge monotone along rivers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_discharge_monotone_along_rivers(seed: int) -> None:
    """Water only accumulates downstream: discharge is non-decreasing along each river."""
    ctx, rivers, receiver, discharge, is_river, river_id = _run(seed)

    for river in rivers:
        d = river.discharge
        for k in range(len(d) - 1):
            assert d[k] <= d[k + 1], (
                f"river {river.id} non-monotone at step {k}: "
                f"{d[k]:.4f} > {d[k + 1]:.4f}"
            )


# ---------------------------------------------------------------------------
# Step 3 — Tributary discharge invariant
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_tributary_of_larger_discharge(seed: int) -> None:
    """tributary_of never points at a river with smaller maximum discharge."""
    ctx, rivers, receiver, discharge, is_river, river_id = _run(seed)

    river_by_id = {r.id: r for r in rivers}
    for river in rivers:
        if river.tributary_of is not None:
            trunk = river_by_id.get(river.tributary_of)
            assert trunk is not None, (
                f"river {river.id} tributary_of={river.tributary_of} not found"
            )
            assert river.discharge.max() < trunk.discharge.max(), (
                f"river {river.id} (max={river.discharge.max():.2f}) -> "
                f"trunk {trunk.id} (max={trunk.discharge.max():.2f})"
            )


# ---------------------------------------------------------------------------
# Step 3 — River mouths terminate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_river_mouths_terminate(seed: int) -> None:
    """Every river's mouth is either -1 (ocean) or a cell that is not a river cell."""
    ctx, rivers, receiver, discharge, is_river, river_id = _run(seed)

    is_lake = ctx.fields.is_lake
    for river in rivers:
        mouth = river.mouth
        if mouth < 0:
            # Ocean mouth (receiver == -1) — valid termination.
            continue
        # A non-negative mouth must be a valid spill point: a lake cell, or a
        # non-river cell.  A tributary's mouth is its own last cell, which is a
        # river cell — but then its receiver is the trunk it feeds into.
        is_lake_mouth = is_lake is not None and bool(is_lake[mouth])
        is_tributary_last_cell = (
            bool(is_river[mouth]) and river.tributary_of is not None
        )
        assert is_lake_mouth or not is_river[mouth] or is_tributary_last_cell, (
            f"river {river.id} mouth={mouth} is a river cell but the river is "
            f"not a tributary — it should have continued"
        )


# ---------------------------------------------------------------------------
# Step 3 — river_id stamps fields correctly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_river_id_stamped_on_field(seed: int) -> None:
    """river_id per cell matches the river that owns each cell."""
    ctx, rivers, receiver, discharge, is_river, river_id = _run(seed)

    for river in rivers:
        for cell in river.cells:
            assert river_id[cell] == river.id, (
                f"river_id[{cell}]={river_id[cell]} != river.id={river.id}"
            )

    # Non-river cells should be -1
    non_river_mask = ~is_river
    assert int((river_id[non_river_mask] == -1).sum()) == int(non_river_mask.sum()), (
        "non-river cells should have river_id == -1"
    )


# ---------------------------------------------------------------------------
# Step 4 — Lake outlets reach the ocean
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_lake_outlets_reach_ocean(seed: int) -> None:
    """Following receiver from each non-terminal outlet hits base level in bounded steps."""
    _world, ctx = WorldgenPipeline(FAST_CONFIG).run_debug(seed=seed, size=FAST_SIZE)
    receiver = ctx.fields.receiver
    n = len(receiver)

    for lake in ctx.lakes:
        if lake.outlet_cell is None:
            continue  # terminal (endorheic) lake — no outlet to trace

        cell = int(lake.outlet_cell)
        seen: set[int] = set()
        steps = 0
        while cell >= 0 and steps <= n:
            assert cell not in seen, (
                f"lake {lake.id} outlet chain cycled at cell {cell}"
            )
            seen.add(cell)
            cell = int(receiver[cell])
            steps += 1

        assert cell == -1, (
            f"lake {lake.id} outlet did not reach base level within {n} steps"
        )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_same_seed_same_rivers(seed: int) -> None:
    """WorldgenPipeline is deterministic: same seed produces identical rivers."""
    ctx_a, rivers_a, receiver_a, discharge_a, is_river_a, river_id_a = _run(seed)
    ctx_b, rivers_b, receiver_b, discharge_b, is_river_b, river_id_b = _run(seed)

    assert len(rivers_a) == len(rivers_b), "different number of rivers"

    for ra, rb in zip(rivers_a, rivers_b):
        assert ra.id == rb.id
        assert ra.cells == rb.cells
        assert np.array_equal(ra.discharge, rb.discharge)
        assert ra.mouth == rb.mouth
        assert ra.tributary_of == rb.tributary_of

    assert np.array_equal(river_id_a, river_id_b)
    assert np.array_equal(is_river_a, is_river_b)


# ---------------------------------------------------------------------------
# WorldData contract — tile-side river ids reference real rivers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_tile_river_ids_reference_world_rivers(seed: int) -> None:
    """Every stamped tile river_id resolves to a River in WorldData.rivers."""
    world = WorldgenPipeline(FAST_CONFIG).run(seed=seed, size=FAST_SIZE)
    known_ids = {river.id for river in world.rivers}
    stamped = {int(rid) for rid in np.unique(world.grid.river_id) if rid >= 0}
    assert stamped <= known_ids, "tile river_id has no matching River object"
