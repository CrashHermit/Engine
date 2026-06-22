"""Phase 0 foundation invariants: determinism, mesh graph, torus noise."""

from dataclasses import fields as dataclass_fields

import numpy as np
import pytest

from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.fields import GridFields, MeshFields
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.noise.rng import NoiseSource, field_offset
from src.worldgen.pipeline import WorldgenPipeline

FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=500))
FAST_SIZE = 50


def _run_pipeline(seed: int) -> tuple:
    """Build a small world and return (ctx, nearest, grid)."""
    ctx = WorldgenPipeline(FAST_CONFIG).run(seed=seed, size=FAST_SIZE)
    nearest = nearest_cell_per_tile(ctx.geometry, size=ctx.config.size)
    grid = bake_to_grid(ctx.fields, nearest)
    return ctx, nearest, grid


def _assert_field_arrays_equal(
    a: MeshFields | GridFields,
    b: MeshFields | GridFields,
) -> None:
    """Assert every SoA field array matches between two field bundles."""
    # Iterate the bundle's own fields: GridFields is a subset of MeshFields
    # (mesh-side intermediates like insolation are not baked to the grid).
    for f in dataclass_fields(type(a)):
        assert np.array_equal(getattr(a, f.name), getattr(b, f.name))


def _assert_geometry_equal(a: MeshGeometry, b: MeshGeometry) -> None:
    """Assert mesh layout and CSR adjacency are identical."""
    assert a.width == b.width and a.height == b.height
    assert np.array_equal(a.sites, b.sites)
    assert np.array_equal(a.neighbor_indices, b.neighbor_indices)
    assert np.array_equal(a.neighbor_offsets, b.neighbor_offsets)


def test_same_seed_produces_identical_world() -> None:
    """Determinism: pipeline + bake are pure functions of seed."""
    ctx_a, nearest_a, grid_a = _run_pipeline(seed=7)
    ctx_b, nearest_b, grid_b = _run_pipeline(seed=7)

    _assert_field_arrays_equal(ctx_a.fields, ctx_b.fields)
    _assert_geometry_equal(ctx_a.geometry, ctx_b.geometry)
    assert np.array_equal(nearest_a, nearest_b)
    _assert_field_arrays_equal(grid_a, grid_b)


def test_mesh_adjacency_is_symmetric() -> None:
    """Every Delaunay edge appears in both cells' neighbor lists."""
    geometry = build_mesh(
        seed=1,
        cell_count=500,
        lloyd_iterations=2,
        width=50.0,
        height=50.0,
    )
    cell_id: int
    neighbor_id: int
    for cell_id in range(geometry.n_cells):
        neighbors = geometry.neighbors_of(cell_id)
        assert len(neighbors) >= 3
        for neighbor_id in neighbors:
            assert cell_id in set(geometry.neighbors_of(int(neighbor_id)))


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
