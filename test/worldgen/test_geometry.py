"""Geometry invariants: CSR well-formedness, adjacency symmetry, torus noise wrap."""

import numpy as np
import pytest

from src.worldgen.geometry.mesh import build_mesh
from src.worldgen.noise.rng import NoiseSource, field_offset

CELL_COUNT: int = 500
SEEDS: list[int] = [1, 7, 42]


def _mesh(seed: int):
    """Build a small torus mesh for the given seed."""
    return build_mesh(
        seed=seed, cell_count=CELL_COUNT, lloyd_iterations=2, width=50.0, height=50.0
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_csr_well_formed(seed: int) -> None:
    """Offsets are monotone, span the indices, and every neighbor id is valid."""
    geometry = _mesh(seed)
    n = geometry.n_cells
    offsets = geometry.neighbor_offsets
    indices = geometry.neighbor_indices

    assert offsets.shape[0] == n + 1
    assert int(offsets[0]) == 0
    assert int(offsets[-1]) == indices.shape[0]
    assert np.all(np.diff(offsets) >= 0), "offsets must be non-decreasing"
    assert np.all(indices >= 0) and np.all(indices < n)


@pytest.mark.parametrize("seed", SEEDS)
def test_mesh_adjacency_is_symmetric(seed: int) -> None:
    """Every Delaunay edge appears in both endpoints' neighbor lists."""
    geometry = _mesh(seed)
    cell_id: int
    neighbor_id: int
    for cell_id in range(geometry.n_cells):
        neighbors = geometry.neighbors_of(cell_id)
        assert len(neighbors) >= 3, "torus mesh cells have at least 3 neighbors"
        for neighbor_id in neighbors:
            assert cell_id in set(geometry.neighbors_of(int(neighbor_id)))


@pytest.mark.parametrize("seed", SEEDS)
def test_no_self_loops(seed: int) -> None:
    """A cell is never its own neighbor."""
    geometry = _mesh(seed)
    cell_id: int
    for cell_id in range(geometry.n_cells):
        assert cell_id not in set(int(n) for n in geometry.neighbors_of(cell_id))


@pytest.mark.parametrize("frequency", [1.0, 4.0, 8.0])
@pytest.mark.parametrize("field_id", [0, 1, 3])
def test_noise_wraps_along_x(frequency: float, field_id: int) -> None:
    """Torus noise is continuous across the x seam."""
    width, height = 100.0, 50.0
    noise = NoiseSource(seed=42, width=width, height=height)
    offset = field_offset(field_id)
    left = noise.sample(0.0, 25.0, frequency, offset)
    right = noise.sample(width, 25.0, frequency, offset)
    assert np.isclose(left, right, atol=1e-6)


@pytest.mark.parametrize("frequency", [1.0, 4.0, 8.0])
@pytest.mark.parametrize("field_id", [0, 1, 3])
def test_noise_wraps_along_y(frequency: float, field_id: int) -> None:
    """Torus noise is continuous across the y seam."""
    width, height = 100.0, 50.0
    noise = NoiseSource(seed=42, width=width, height=height)
    offset = field_offset(field_id)
    bottom = noise.sample(50.0, 0.0, frequency, offset)
    top = noise.sample(50.0, height, frequency, offset)
    assert np.isclose(bottom, top, atol=1e-6)
