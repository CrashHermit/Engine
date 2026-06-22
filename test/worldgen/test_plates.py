"""Plate partition invariants: coverage, connectivity, determinism."""

import numpy as np
import pytest

from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.terrain.plates import UNCLAIMED, build_plates
from src.worldgen.types import Int32Array

N_PLATES: int = 8
PLATE_SEED: int = 42
MESH_SEED: int = 1
CELL_COUNT: int = 500
MESH_WIDTH: float = 50.0
MESH_HEIGHT: float = 50.0
LLOYD_ITERATIONS: int = 2
DEFAULT_GROWTH_RAGGEDNESS: float = 2.0


def _small_mesh() -> MeshGeometry:
    """Build a fixed small mesh for plate tests."""
    return build_mesh(
        seed=MESH_SEED,
        cell_count=CELL_COUNT,
        lloyd_iterations=LLOYD_ITERATIONS,
        width=MESH_WIDTH,
        height=MESH_HEIGHT,
    )


def _build_plate_ids(
    *,
    seed: int = PLATE_SEED,
    growth_raggedness: float = DEFAULT_GROWTH_RAGGEDNESS,
    geometry: MeshGeometry | None = None,
    n_plates: int = N_PLATES,
) -> Int32Array:
    """Run build_plates on the shared test mesh (or a caller-supplied geometry)."""
    mesh: MeshGeometry = geometry if geometry is not None else _small_mesh()
    return build_plates(
        geometry=mesh,
        n_plates=n_plates,
        seed=seed,
        growth_raggedness=growth_raggedness,
    )


def _cells_reachable_within_plate(
    geometry: MeshGeometry,
    plate_id: Int32Array,
    plate: int,
) -> set[int]:
    """Return all cells in ``plate`` reachable from one seed via same-plate edges."""
    member_cells: Int32Array = np.flatnonzero(plate_id == plate).astype(np.int32)
    assert member_cells.size > 0

    start_cell: int = int(member_cells[0])
    visited: set[int] = {start_cell}
    frontier: list[int] = [start_cell]

    while frontier:
        cell_id: int = frontier.pop()
        neighbor_id: int
        for neighbor_id in geometry.neighbors_of(cell_id):
            neighbor_id: int = int(neighbor_id)
            if plate_id[neighbor_id] != plate:
                continue
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            frontier.append(neighbor_id)

    return visited


def test_every_cell_claimed() -> None:
    """All cells receive a valid plate id."""
    plate_id: Int32Array = _build_plate_ids()
    assert (plate_id != UNCLAIMED).all()
    assert int(plate_id.min()) >= 0
    assert int(plate_id.max()) < N_PLATES


def test_each_plate_region_is_connected() -> None:
    """Cells sharing a plate id form one contiguous region on the mesh graph."""
    geometry: MeshGeometry = _small_mesh()
    plate_id: Int32Array = _build_plate_ids(geometry=geometry)

    plate: int
    for plate in range(N_PLATES):
        member_cells: Int32Array = np.flatnonzero(a=plate_id == plate).astype(np.int32)
        assert member_cells.size > 0
        reachable_cells: set[int] = _cells_reachable_within_plate(
            geometry=geometry,
            plate_id=plate_id,
            plate=plate,
        )
        expected_cells: set[int] = {int(cell_id) for cell_id in member_cells}
        assert reachable_cells == expected_cells


def test_same_seed_is_deterministic() -> None:
    """Plate partition is a pure function of seed and config."""
    plate_id_a: Int32Array = _build_plate_ids(seed=PLATE_SEED)
    plate_id_b: Int32Array = _build_plate_ids(seed=PLATE_SEED)
    assert np.array_equal(a1=plate_id_a, a2=plate_id_b)


def test_different_seeds_differ() -> None:
    """Different seeds produce different partitions."""
    plate_id_a: Int32Array = _build_plate_ids(seed=1)
    plate_id_b: Int32Array = _build_plate_ids(seed=2)
    assert not np.array_equal(a1=plate_id_a, a2=plate_id_b)


def test_n_plates_must_be_positive() -> None:
    """Reject invalid plate counts."""
    geometry: MeshGeometry = _small_mesh()
    with pytest.raises(ValueError, match="n_plates must be at least 1"):
        build_plates(
            geometry=geometry,
            n_plates=0,
            seed=PLATE_SEED,
            growth_raggedness=DEFAULT_GROWTH_RAGGEDNESS,
        )


def test_n_plates_cannot_exceed_cell_count() -> None:
    """Reject more plates than mesh cells."""
    geometry: MeshGeometry = _small_mesh()
    with pytest.raises(ValueError, match="cannot exceed cell count"):
        build_plates(
            geometry=geometry,
            n_plates=geometry.n_cells + 1,
            seed=PLATE_SEED,
            growth_raggedness=DEFAULT_GROWTH_RAGGEDNESS,
        )
