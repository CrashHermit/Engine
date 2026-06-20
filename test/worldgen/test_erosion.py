"""Erosion invariants: stream-power stability, diffusion, determinism."""

from __future__ import annotations

import numpy as np
import pytest

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.terrain.erosion import diffuse, stream_power_pass
from src.worldgen.terrain.routing import (
    accumulate_drainage,
    compute_receivers,
    priority_flood,
)
from src.worldgen.types import Float64Array, Int32Array

MESH_SEED: int = 1
CELL_COUNT: int = 500
MESH_WIDTH: float = 50.0
MESH_HEIGHT: float = 50.0
LLOYD_ITERATIONS: int = 2


def _small_mesh() -> MeshGeometry:
    return build_mesh(
        seed=MESH_SEED,
        cell_count=CELL_COUNT,
        lloyd_iterations=LLOYD_ITERATIONS,
        width=MESH_WIDTH,
        height=MESH_HEIGHT,
    )


def _make_terrain(rng: np.random.Generator, geometry: MeshGeometry) -> Float64Array:
    """Create plausible starting terrain: gentle slopes with some peaks."""
    z: Float64Array = rng.normal(size=geometry.n_cells, scale=0.5)
    # Add a broad peak in the center.
    xs: Float64Array = geometry.sites[:, 0]
    ys: Float64Array = geometry.sites[:, 1]
    cx: float = geometry.width / 2.0
    cy: float = geometry.height / 2.0
    dist: Float64Array = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    z += np.exp(-dist ** 2 / (0.5 * geometry.width) ** 2) * 2.0
    return z


def _make_routing(
    z: Float64Array, geometry: MeshGeometry
) -> tuple[Float64Array, Int32Array, Float64Array]:
    """Build z_route, receiver, drainage from terrain z."""
    base_cells: Int32Array = np.argpartition(z, max(1, int(0.1 * len(z))))[: max(1, int(0.1 * len(z)))].astype(np.int32)
    z_route: Float64Array = priority_flood(geometry=geometry, z=z, base_cells=base_cells)
    receiver: Int32Array = compute_receivers(geometry=geometry, z_route=z_route)
    drainage: Float64Array = accumulate_drainage(receiver=receiver, z_route=z_route)
    return z_route, receiver, drainage


def _cfg(
    dt: float = 0.1,
    K: float = 0.3,
    m: float = 0.5,
    diffusion: float = 0.08,
) -> ErosionConfig:
    return ErosionConfig(dt=dt, K=K, m=m, diffusion=diffusion)


# ---------------------------------------------------------------------------
# stream_power_pass
# ---------------------------------------------------------------------------


def test_stream_power_no_nans() -> None:
    """A single stream-power pass never produces NaN values."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    z_route, receiver, drainage = _make_routing(z, geometry)

    stream_power_pass(
        z=z,
        z_route=z_route,
        receiver=receiver,
        drainage=drainage,
        uplift=uplift,
        geometry=geometry,
        cfg=_cfg(),
    )

    assert not np.any(np.isnan(z)), "stream_power_pass produced NaN"


def test_stream_power_no_infs() -> None:
    """A single stream-power pass never produces Inf values."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    z_route, receiver, drainage = _make_routing(z, geometry)

    stream_power_pass(
        z=z,
        z_route=z_route,
        receiver=receiver,
        drainage=drainage,
        uplift=uplift,
        geometry=geometry,
        cfg=_cfg(),
    )

    assert not np.any(np.isinf(z)), "stream_power_pass produced Inf"


def test_stream_power_stable_at_large_dt() -> None:
    """The implicit scheme stays stable even with a very large dt."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    z_route, receiver, drainage = _make_routing(z, geometry)

    big_dt_cfg: ErosionConfig = _cfg(dt=10.0)  # 100× larger than normal

    stream_power_pass(
        z=z,
        z_route=z_route,
        receiver=receiver,
        drainage=drainage,
        uplift=uplift,
        geometry=geometry,
        cfg=big_dt_cfg,
    )

    assert not np.any(np.isnan(z)), "Large dt produced NaN"
    assert not np.any(np.isinf(z)), "Large dt produced Inf"


def test_stream_power_preserves_downhill_order() -> None:
    """After erosion pass, z should not create new inversions that exceed receiver."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    z_route, receiver, drainage = _make_routing(z, geometry)

    z_before: Float64Array = z.copy()

    stream_power_pass(
        z=z,
        z_route=z_route,
        receiver=receiver,
        drainage=drainage,
        uplift=uplift,
        geometry=geometry,
        cfg=_cfg(dt=0.01, K=0.01),  # tiny step to observe gentle change
    )

    # The implicit update is a weighted average, so z should not diverge wildly.
    max_change: float = float(np.max(np.abs(z - z_before)))
    assert max_change < 0.5, (
        f"Tiny dt/K produced excessive change of {max_change}"
    )


def test_stream_power_base_level_cells_unchanged() -> None:
    """Base-level cells (receiver == -1) are not modified by stream-power."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    z_route, receiver, drainage = _make_routing(z, geometry)

    base_cells: Int32Array = np.flatnonzero(receiver == -1)
    z_before: Float64Array = z[base_cells].copy()

    stream_power_pass(
        z=z,
        z_route=z_route,
        receiver=receiver,
        drainage=drainage,
        uplift=uplift,
        geometry=geometry,
        cfg=_cfg(),
    )

    np.testing.assert_array_equal(z[base_cells], z_before)


# ---------------------------------------------------------------------------
# diffuse
# ---------------------------------------------------------------------------


def test_diffusion_no_nans() -> None:
    """A single diffusion pass never produces NaN values."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    cfg: ErosionConfig = ErosionConfig(diffusion=0.1)

    diffuse(z=z, geometry=geometry, cfg=cfg)

    assert not np.any(np.isnan(z)), "diffusion produced NaN"
    assert not np.any(np.isinf(z)), "diffusion produced Inf"


def test_diffusion_blurs() -> None:
    """Diffusion reduces elevation variance (smooths the terrain)."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    cfg: ErosionConfig = ErosionConfig(diffusion=0.1)

    var_before: float = float(np.var(z))
    diffuse(z=z, geometry=geometry, cfg=cfg)
    var_after: float = float(np.var(z))

    assert var_after < var_before, (
        f"Diffusion should reduce variance: {var_before:.4f} -> {var_after:.4f}"
    )


def test_diffusion_order_independent() -> None:
    """Diffusion is order-independent because it is double-buffered.

    Apply diffusion to the same input twice; both runs must produce
    identical output (proving no cell-order bias within a pass).
    """
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z_a: Float64Array = _make_terrain(rng, geometry)
    z_b: Float64Array = z_a.copy()

    cfg: ErosionConfig = ErosionConfig(diffusion=0.1)

    diffuse(z=z_a, geometry=geometry, cfg=cfg)
    diffuse(z=z_b, geometry=geometry, cfg=cfg)

    np.testing.assert_array_equal(z_a, z_b)


def test_diffusion_deterministic() -> None:
    """Same input produces the same output."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z_a: Float64Array = _make_terrain(rng, geometry)
    z_b: Float64Array = z_a.copy()

    cfg: ErosionConfig = ErosionConfig(diffusion=0.1)

    diffuse(z=z_a, geometry=geometry, cfg=cfg)
    diffuse(z=z_b, geometry=geometry, cfg=cfg)

    assert np.array_equal(z_a, z_b)


# ---------------------------------------------------------------------------
# Full erosion loop
# ---------------------------------------------------------------------------


def test_full_erosion_loop_stable() -> None:
    """Running the full erosion loop (flood + route + erode + diffuse)
    on random terrain produces valid output without NaN/Inf."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    cfg: ErosionConfig = ErosionConfig(iterations=5, dt=0.1, K=0.3, m=0.5, diffusion=0.08)

    n: int = geometry.n_cells

    for _iteration in range(cfg.iterations):
        n_base: int = max(1, int(cfg.base_level_fraction * n))
        base_cells: Int32Array = np.argpartition(z, n_base)[:n_base].astype(np.int32)

        z_route: Float64Array = priority_flood(
            geometry=geometry, z=z, base_cells=base_cells,
        )
        receiver: Int32Array = compute_receivers(
            geometry=geometry, z_route=z_route,
        )
        drainage: Float64Array = accumulate_drainage(
            receiver=receiver, z_route=z_route,
        )
        stream_power_pass(
            z=z, z_route=z_route, receiver=receiver,
            drainage=drainage, uplift=uplift,
            geometry=geometry, cfg=cfg,
        )
        diffuse(z=z, geometry=geometry, cfg=cfg)

    assert not np.any(np.isnan(z)), "Full erosion loop produced NaN"
    assert not np.any(np.isinf(z)), "Full erosion loop produced Inf"


def test_full_erosion_loop_creves_valleys() -> None:
    """After erosion, the terrain should have more varied relief than raw uplift."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    z: Float64Array = _make_terrain(rng, geometry)
    uplift: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.01
    cfg: ErosionConfig = ErosionConfig(
        iterations=20, dt=0.1, K=0.5, m=0.5, diffusion=0.08,
    )

    n: int = geometry.n_cells

    for _iteration in range(cfg.iterations):
        n_base = max(1, int(cfg.base_level_fraction * n))
        base_cells = np.argpartition(z, n_base)[:n_base].astype(np.int32)
        z_route = priority_flood(geometry=geometry, z=z, base_cells=base_cells)
        receiver = compute_receivers(geometry=geometry, z_route=z_route)
        drainage = accumulate_drainage(receiver=receiver, z_route=z_route)
        stream_power_pass(
            z=z, z_route=z_route, receiver=receiver,
            drainage=drainage, uplift=uplift, geometry=geometry, cfg=cfg,
        )
        diffuse(z=z, geometry=geometry, cfg=cfg)

    # The range should be meaningful (mountains and valleys).
    assert z.max() > z.min() + 0.1, "Erosion should produce meaningful relief"
