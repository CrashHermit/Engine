"""Routing invariants: priority flood, receivers, drainage accumulation."""

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.terrain.routing import (
    accumulate_drainage,
    compute_receivers,
    priority_flood,
)
from src.worldgen.types import Float64Array, Int32Array

MESH_SEED: int = 1
N_PLATES: int = 8
PLATE_SEED: int = 42
CELL_COUNT: int = 500
MESH_WIDTH: float = 50.0
MESH_HEIGHT: float = 50.0
LLOYD_ITERATIONS: int = 2


def _small_mesh() -> MeshGeometry:
    """Build a fixed small mesh for routing tests."""
    return build_mesh(
        seed=MESH_SEED,
        cell_count=CELL_COUNT,
        lloyd_iterations=LLOYD_ITERATIONS,
        width=MESH_WIDTH,
        height=MESH_HEIGHT,
    )


def _build_base_cells(z: Float64Array, fraction: float = 0.1) -> Int32Array:
    """Return the lowest ``fraction`` percentile of ``z`` as base cells."""
    n: int = len(z)
    n_base: int = max(1, int(fraction * n))
    return np.argpartition(z, n_base)[:n_base].astype(np.int32)


# ---------------------------------------------------------------------------
# priority_flood
# ---------------------------------------------------------------------------


def test_priority_flood_reaches_all_cells() -> None:
    """Every cell gets a finite z_route value — no cells are left behind."""
    geometry: MeshGeometry = _small_mesh()
    z: Float64Array = np.random.default_rng(seed=42).normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )

    assert not np.any(np.isnan(z_route))
    assert not np.any(np.isinf(z_route))
    assert z_route.shape == (geometry.n_cells,)


def test_priority_flood_water_surface_is_non_decreasing() -> None:
    """Water cannot flow downward through the routed surface."""
    geometry: MeshGeometry = _small_mesh()
    z: Float64Array = np.random.default_rng(seed=42).normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )

    # z_route >= z everywhere (water fills bowls to at least ground level).
    assert np.all(z_route >= z - 1e-10)


def test_priority_flood_base_cells_have_exact_z() -> None:
    """Base (seed) cells get z_route == z exactly — water starts at ground."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )

    for cell_id in base_cells:
        np.testing.assert_allclose(z_route[cell_id], z[cell_id], atol=1e-14)


# ---------------------------------------------------------------------------
# compute_receivers
# ---------------------------------------------------------------------------


def test_receivers_no_cycles() -> None:
    """Following receiver from any cell reaches a base-level cell (-1) in finite steps."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )
    receiver: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route,
    )

    max_steps: int = geometry.n_cells
    cell_id: int
    for cell_id in range(geometry.n_cells):
        steps: int = 0
        current: int = cell_id
        while current >= 0 and steps < max_steps:
            current = int(receiver[current])
            steps += 1
        assert steps <= max_steps, (
            f"Cycle or dead end at cell {cell_id}: followed receiver for {steps} steps"
        )


def test_receivers_are_downhill() -> None:
    """Every cell with a receiver points to a neighbour with lower z_route."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )
    receiver: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route,
    )

    cell_id: int
    for cell_id in range(geometry.n_cells):
        r: int = int(receiver[cell_id])
        if r < 0:
            continue
        assert z_route[r] < z_route[cell_id] + 1e-10, (
            f"Cell {cell_id} has receiver {r} with non-lower z_route"
        )


def test_receivers_base_level_reach_pits() -> None:
    """Every base-level cell eventually reaches a pit (receiver == -1).

    Base cells are the lowest elevation percentile, but they may have
    receivers pointing to other base cells.  What matters is that
    following the receiver chain from any base cell terminates at a pit.
    """
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )
    receiver: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route,
    )

    max_steps: int = geometry.n_cells
    for cell_id in base_cells:
        steps: int = 0
        current: int = int(cell_id)
        while current >= 0 and steps < max_steps:
            current = int(receiver[current])
            steps += 1
        assert steps <= max_steps, (
            f"Base cell {cell_id} does not reach a pit within {max_steps} steps"
        )


# ---------------------------------------------------------------------------
# accumulate_drainage
# ---------------------------------------------------------------------------


def test_drainage_all_positive() -> None:
    """Every cell has drainage >= 1 (each cell contributes at least itself)."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )
    receiver: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route,
    )
    drainage: Float64Array = accumulate_drainage(
        receiver=receiver,
        z_route=z_route,
    )

    assert np.all(drainage >= 1.0)


def test_drainage_monotonic_along_receiver() -> None:
    """Drainage is non-decreasing along receiver chains.

    Since every cell contributes 1 and passes its accumulated total
    downstream, each cell's receiver must have drainage >= its own.
    """
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route: Float64Array
    z_route, _ = priority_flood(
        geometry=geometry,
        z=z,
        base_cells=base_cells,
    )
    receiver: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route,
    )
    drainage: Float64Array = accumulate_drainage(
        receiver=receiver,
        z_route=z_route,
    )

    cell_id: int
    for cell_id in range(geometry.n_cells):
        r: int = int(receiver[cell_id])
        if r < 0:
            continue
        assert drainage[r] >= drainage[cell_id] - 1e-12, (
            f"Cell {cell_id} has drainage {drainage[cell_id]:.2f} but receiver {r} has {drainage[r]:.2f}"
        )


def test_drainage_deterministic() -> None:
    """Running drainage on the same receiver/z_route twice gives the same result."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = rng.normal(size=geometry.n_cells)
    base_cells: Int32Array = _build_base_cells(z)

    z_route_a: Float64Array
    z_route_a, _ = priority_flood(
        geometry=geometry,
        z=z.copy(),
        base_cells=base_cells,
    )
    receiver_a: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route_a,
    )
    drainage_a: Float64Array = accumulate_drainage(
        receiver=receiver_a,
        z_route=z_route_a,
    )

    z_route_b: Float64Array
    z_route_b, _ = priority_flood(
        geometry=geometry,
        z=z.copy(),
        base_cells=base_cells,
    )
    receiver_b: Int32Array = compute_receivers(
        geometry=geometry,
        z_route=z_route_b,
    )
    drainage_b: Float64Array = accumulate_drainage(
        receiver=receiver_b,
        z_route=z_route_b,
    )

    assert np.array_equal(drainage_a, drainage_b)
    assert np.array_equal(receiver_a, receiver_b)
    assert np.array_equal(z_route_a, z_route_b)
