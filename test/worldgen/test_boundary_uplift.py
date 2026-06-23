"""Boundary uplift invariants: collision belts, rift seams, clamping, determinism."""

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import NoiseSource, subseed
from src.worldgen.terrain.boundaries import BoundaryFacts, classify_boundaries
from src.worldgen.terrain.boundary_uplift import apply_boundary_uplift
from src.worldgen.terrain.plates import build_plates
from src.worldgen.terrain.plate_personalities import (
    assign_plate_personalities,
    fill_uplift_from_plates,
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
    return build_mesh(
        seed=MESH_SEED,
        cell_count=CELL_COUNT,
        lloyd_iterations=LLOYD_ITERATIONS,
        width=MESH_WIDTH,
        height=MESH_HEIGHT,
    )


def _setup_uplift(
    geometry: MeshGeometry,
) -> tuple[BoundaryFacts, Float64Array, PlatesConfig]:
    """Run plates + personality + classification to get facts and initial uplift."""
    plate_id = build_plates(
        geometry=geometry,
        n_plates=N_PLATES,
        seed=PLATE_SEED,
        growth_raggedness=2.0,
    )
    props = assign_plate_personalities(
        n_plates=N_PLATES,
        seed=PLATE_SEED,
        config=PlatesConfig(),
    )
    facts: BoundaryFacts = classify_boundaries(
        geometry=geometry,
        plate_id=plate_id,
        properties=props,
    )
    uplift: Float64Array = fill_uplift_from_plates(
        plate_id=plate_id,
        base_uplift=props.base_uplift,
    )
    cfg: PlatesConfig = PlatesConfig()
    return facts, uplift, cfg


def _make_noise_fields(
    geometry: MeshGeometry, seed: int
) -> tuple[FractalField, FractalField]:
    """Create belt_noise and uplift_noise FractalField instances."""
    sub_seed: int = subseed(seed=seed, name="boundary_uplift")
    belt_noise: FractalField = FractalField(
        sampler=NoiseSource(seed=sub_seed, width=geometry.width, height=geometry.height),
        field_id=0,
        octaves=3,
    )
    sub_seed_2: int = subseed(seed=seed, name="uplift_floor")
    uplift_noise: FractalField = FractalField(
        sampler=NoiseSource(seed=sub_seed_2, width=geometry.width, height=geometry.height),
        field_id=0,
        octaves=3,
    )
    return belt_noise, uplift_noise


# ---------------------------------------------------------------------------
# Collision belts
# ---------------------------------------------------------------------------


def test_collision_belts_increase_uplift() -> None:
    """Boundary uplift adds to existing uplift — some cells must increase."""
    geometry: MeshGeometry = _small_mesh()
    facts, uplift, cfg = _setup_uplift(geometry)
    initial_uplift: Float64Array = uplift.copy()
    belt_noise, uplift_noise = _make_noise_fields(geometry, PLATE_SEED)

    apply_boundary_uplift(
        geometry=geometry,
        facts=facts,
        uplift=uplift,
        config=cfg,
        belt_noise=belt_noise,
        uplift_noise=uplift_noise,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    assert np.any(uplift > initial_uplift), (
        "Expected some uplift increase from collision belts"
    )


def test_rift_seams_decrease_uplift() -> None:
    """Boundary uplift subtracts from uplift along divergent boundaries."""
    geometry: MeshGeometry = _small_mesh()
    facts, uplift, cfg = _setup_uplift(geometry)
    initial_uplift: Float64Array = uplift.copy()
    belt_noise, uplift_noise = _make_noise_fields(geometry, PLATE_SEED)

    apply_boundary_uplift(
        geometry=geometry,
        facts=facts,
        uplift=uplift,
        config=cfg,
        belt_noise=belt_noise,
        uplift_noise=uplift_noise,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    assert np.any(uplift < initial_uplift), (
        "Expected some uplift decrease from rift seams"
    )


# ---------------------------------------------------------------------------
# Clamping
# ---------------------------------------------------------------------------


def test_uplift_never_negative() -> None:
    """After boundary uplift, no cell has negative uplift (clamped)."""
    geometry: MeshGeometry = _small_mesh()
    facts, uplift, cfg = _setup_uplift(geometry)
    belt_noise, uplift_noise = _make_noise_fields(geometry, PLATE_SEED)

    apply_boundary_uplift(
        geometry=geometry,
        facts=facts,
        uplift=uplift,
        config=cfg,
        belt_noise=belt_noise,
        uplift_noise=uplift_noise,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    assert np.all(uplift >= 0.0), (
        "Uplift must be clamped to >= 0 after boundary uplift"
    )


# ---------------------------------------------------------------------------
# Smear produces wide belts
# ---------------------------------------------------------------------------


def test_belts_wider_than_one_cell() -> None:
    """Collision belts span multiple cells (smear is not a single-cell line)."""
    geometry: MeshGeometry = _small_mesh()
    facts, uplift, cfg = _setup_uplift(geometry)
    initial_uplift: Float64Array = uplift.copy()
    belt_noise, uplift_noise = _make_noise_fields(geometry, PLATE_SEED)

    apply_boundary_uplift(
        geometry=geometry,
        facts=facts,
        uplift=uplift,
        config=cfg,
        belt_noise=belt_noise,
        uplift_noise=uplift_noise,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    # At least one cell's uplift changed, and the change should affect
    # a contiguous group of cells (belt), not just a single boundary cell.
    changed: Int32Array = np.flatnonzero(uplift != initial_uplift)
    assert len(changed) > 1, (
        f"Expected belt smearing across multiple cells, got {len(changed)} changed"
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_boundary_uplift_deterministic() -> None:
    """Same seed produces identical uplift."""
    geometry: MeshGeometry = _small_mesh()
    facts, uplift_a, cfg = _setup_uplift(geometry)
    belt_noise_a, uplift_noise_a = _make_noise_fields(geometry, PLATE_SEED)

    apply_boundary_uplift(
        geometry=geometry,
        facts=facts,
        uplift=uplift_a,
        config=cfg,
        belt_noise=belt_noise_a,
        uplift_noise=uplift_noise_a,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    facts_2, uplift_b, cfg_2 = _setup_uplift(geometry)
    belt_noise_b, uplift_noise_b = _make_noise_fields(geometry, PLATE_SEED)

    apply_boundary_uplift(
        geometry=geometry,
        facts=facts_2,
        uplift=uplift_b,
        config=cfg_2,
        belt_noise=belt_noise_b,
        uplift_noise=uplift_noise_b,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    np.testing.assert_array_equal(uplift_a, uplift_b)


# ---------------------------------------------------------------------------
# Config parameters affect output
# ---------------------------------------------------------------------------


def test_belt_strength_affects_uplift() -> None:
    """Higher belt_strength produces more uplift increase."""
    geometry: MeshGeometry = _small_mesh()
    facts, uplift_a, cfg_low = _setup_uplift(geometry)
    belt_noise, uplift_noise = _make_noise_fields(geometry, PLATE_SEED)

    cfg_low.belt_strength = 0.1
    apply_boundary_uplift(
        geometry=geometry,
        facts=facts,
        uplift=uplift_a,
        config=cfg_low,
        belt_noise=belt_noise,
        uplift_noise=uplift_noise,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    facts_2, uplift_b, cfg_high = _setup_uplift(geometry)
    cfg_high.belt_strength = 1.0
    apply_boundary_uplift(
        geometry=geometry,
        facts=facts_2,
        uplift=uplift_b,
        config=cfg_high,
        belt_noise=belt_noise,
        uplift_noise=uplift_noise,
        frequency=4.0 / min(geometry.width, geometry.height),
    )

    # Higher belt_strength should produce more total uplift increase.
    assert uplift_b.sum() > uplift_a.sum(), (
        "Higher belt_strength should produce more uplift"
    )
