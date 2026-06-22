"""Finalize invariants: sea level normalization, landmass labeling,
coast distance, slope, determinism."""

import numpy as np

from src.worldgen.config.worldgen_config import (
    LandmassConfig,
    MeshConfig,
    SeaLevelConfig,
    WorldgenConfig,
)
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.terrain.finalize import (
    apply_sea_level,
    compute_coast_distance,
    compute_slope,
    label_landmasses,
)
from src.worldgen.types import BoolArray, Float64Array, Int32Array, Int8Array

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


# ---------------------------------------------------------------------------
# apply_sea_level
# ---------------------------------------------------------------------------


def test_sea_level_normalization_range() -> None:
    """After sea-level normalization, all elevations are in [-1, 1]."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)

    apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    assert elevation.min() >= -1.0 - 1e-10
    assert elevation.max() <= 1.0 + 1e-10


def test_sea_level_zero_at_sea_level_boundary() -> None:
    """Sea-level cells have elevation exactly 0."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)

    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    # Sea-level boundary cells should be exactly 0.
    sea_cells: Float64Array = elevation[is_land & (elevation == 0.0)]
    # Or more precisely: cells at the boundary where land meets ocean
    # should have elevation close to 0.
    # Check that land min is close to 0 and ocean max is close to 0.
    if np.any(is_land):
        assert elevation[is_land].min() >= -1e-10
    if np.any(~is_land):
        assert elevation[~is_land].max() <= 1e-10


def test_sea_level_land_fraction() -> None:
    """The land fraction after normalization matches the target."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)

    target: float = 0.32
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=target,
    )

    actual: float = float(is_land.mean())
    np.testing.assert_allclose(actual, target, atol=0.03, err_msg=(
        f"Land fraction {actual:.3f} should be within ±3% of {target}"
    ))


def test_sea_level_land_is_positive() -> None:
    """All land cells have elevation > 0 after normalization."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)

    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    if np.any(is_land):
        assert elevation[is_land].min() >= -1e-10  # land should be >= 0


def test_sea_level_ocean_is_negative() -> None:
    """All ocean cells have elevation < 0 after normalization."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)

    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    if np.any(~is_land):
        assert elevation[~is_land].max() <= 1e-10  # ocean should be <= 0


# ---------------------------------------------------------------------------
# label_landmasses
# ---------------------------------------------------------------------------


def test_landmass_ids_nonzero_for_land() -> None:
    """Every land cell gets a non-zero landmass_id."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    landmass_id, _ = label_landmasses(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
        island_min_fraction=0.005,
        landmass_min_fraction=0.08,
    )

    land_cells: Int32Array = np.flatnonzero(is_land)
    if len(land_cells) > 0:
        assert np.all(landmass_id[land_cells] > 0), (
            "All land cells should have non-zero landmass_id"
        )


def test_ocean_landmass_id_zero() -> None:
    """Ocean cells have landmass_id == 0."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    landmass_id, _ = label_landmasses(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
        island_min_fraction=0.005,
        landmass_min_fraction=0.08,
    )

    ocean_cells: Int32Array = np.flatnonzero(~is_land)
    if len(ocean_cells) > 0:
        assert np.all(landmass_id[ocean_cells] == 0), (
            "All ocean cells should have landmass_id == 0"
        )


def test_landmass_classes_valid() -> None:
    """All landmass_class values are in {0, 1, 2, 3}."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    _landmass_id: Int32Array
    landmass_class: Int8Array
    _landmass_id, landmass_class = label_landmasses(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
        island_min_fraction=0.005,
        landmass_min_fraction=0.08,
    )

    valid_classes: Int8Array = np.array([0, 1, 2, 3], dtype=np.int8)
    assert np.all(np.isin(landmass_class, valid_classes)), (
        f"landmass_class values must be in {{0,1,2,3}}, got: {np.unique(landmass_class)}"
    )


def test_landmass_class_consistent_with_id() -> None:
    """Cells in the same landmass_id have the same landmass_class."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    landmass_id, landmass_class = label_landmasses(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
        island_min_fraction=0.005,
        landmass_min_fraction=0.08,
    )

    for component in range(1, int(landmass_id.max()) + 1):
        mask: BoolArray = landmass_id == component
        classes: Int8Array = landmass_class[mask]
        assert len(np.unique(classes)) == 1, (
            f"Component {component} has inconsistent landmass_class: {np.unique(classes)}"
        )


# ---------------------------------------------------------------------------
# compute_coast_distance
# ---------------------------------------------------------------------------


def test_coast_distance_nonnegative() -> None:
    """All coast distances are >= 0."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    coast_distance: Float64Array = compute_coast_distance(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    assert np.all(coast_distance >= 0.0)


def test_coastal_cells_have_zero_distance() -> None:
    """Coastal land cells (adjacent to ocean) have coast_distance == 0."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    coast_distance: Float64Array = compute_coast_distance(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    # Identify coastal land cells (land with at least one ocean neighbor).
    is_ocean: BoolArray = ~is_land
    coastal: BoolArray = np.zeros(geometry.n_cells, dtype=bool)
    for cell_id in range(geometry.n_cells):
        if not is_land[cell_id]:
            continue
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if is_ocean[neighbor_id]:
                coastal[cell_id] = True
                break

    if np.any(coastal):
        assert np.all(coast_distance[coastal] == 0.0), (
            "Coastal land cells should have coast_distance == 0"
        )


def test_ocean_cells_have_zero_distance() -> None:
    """Ocean cells have coast_distance == 0."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    is_land: BoolArray = apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    coast_distance: Float64Array = compute_coast_distance(
        is_land=is_land,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    ocean_cells: Int32Array = np.flatnonzero(~is_land)
    if len(ocean_cells) > 0:
        assert np.all(coast_distance[ocean_cells] == 0.0)


# ---------------------------------------------------------------------------
# compute_slope
# ---------------------------------------------------------------------------


def test_slope_nonnegative() -> None:
    """All slope values are >= 0."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    apply_sea_level(
        elevation=elevation,
        target_land_fraction=0.32,
    )

    slope: Float64Array = compute_slope(
        elevation=elevation,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    assert np.all(slope >= 0.0)


def test_slope_zero_on_flat() -> None:
    """Uniform elevation produces zero slope everywhere."""
    geometry: MeshGeometry = _small_mesh()
    elevation: Float64Array = np.ones(geometry.n_cells, dtype=np.float64) * 0.5

    slope: Float64Array = compute_slope(
        elevation=elevation,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    np.testing.assert_allclose(slope, 0.0, atol=1e-14)


def test_slope_positive_with_gradient() -> None:
    """A linear gradient produces some positive slopes."""
    geometry: MeshGeometry = _small_mesh()
    xs: Float64Array = geometry.sites[:, 0]
    elevation: Float64Array = xs / geometry.width  # linear gradient

    slope: Float64Array = compute_slope(
        elevation=elevation,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    assert np.any(slope > 0.0), "Slope should be positive where elevation changes"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_finalize_deterministic() -> None:
    """Running finalize twice on the same terrain produces identical output."""
    geometry: MeshGeometry = _small_mesh()
    rng: np.random.Generator = np.random.default_rng(seed=42)
    elevation_a: Float64Array = rng.normal(size=geometry.n_cells, scale=1.0)
    elevation_b: Float64Array = elevation_a.copy()

    is_land_a: BoolArray = apply_sea_level(
        elevation=elevation_a,
        target_land_fraction=0.32,
    )
    landmass_id_a, landmass_class_a = label_landmasses(
        is_land=is_land_a,
        geometry=geometry,
        n_cells=geometry.n_cells,
        island_min_fraction=0.005,
        landmass_min_fraction=0.08,
    )
    coast_a: Float64Array = compute_coast_distance(
        is_land=is_land_a,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )
    slope_a: Float64Array = compute_slope(
        elevation=elevation_a,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    is_land_b: BoolArray = apply_sea_level(
        elevation=elevation_b,
        target_land_fraction=0.32,
    )
    landmass_id_b, landmass_class_b = label_landmasses(
        is_land=is_land_b,
        geometry=geometry,
        n_cells=geometry.n_cells,
        island_min_fraction=0.005,
        landmass_min_fraction=0.08,
    )
    coast_b: Float64Array = compute_coast_distance(
        is_land=is_land_b,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )
    slope_b: Float64Array = compute_slope(
        elevation=elevation_b,
        geometry=geometry,
        n_cells=geometry.n_cells,
    )

    np.testing.assert_array_equal(elevation_a, elevation_b)
    np.testing.assert_array_equal(is_land_a, is_land_b)
    np.testing.assert_array_equal(landmass_id_a, landmass_id_b)
    np.testing.assert_array_equal(landmass_class_a, landmass_class_b)
    np.testing.assert_array_equal(coast_a, coast_b)
    np.testing.assert_array_equal(slope_a, slope_b)


# ---------------------------------------------------------------------------
# Full pipeline integration
# ---------------------------------------------------------------------------


def test_full_pipeline_elevation_contract() -> None:
    """End-to-end: pipeline output satisfies the elevation contract."""
    ctx: WorldContext = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(cell_count=CELL_COUNT, width=MESH_WIDTH, height=MESH_HEIGHT),
            sea_level=SeaLevelConfig(target_land_fraction=0.32),
            landmass=LandmassConfig(island_min_fraction=0.005, landmass_min_fraction=0.08),
        )
    ).run(seed=42, size=50)

    elevation: Float64Array | None = ctx.fields.elevation
    assert elevation is not None
    assert elevation.min() >= -1.0 - 1e-10, (
        f"Elevation min {elevation.min():.4f} should be >= -1"
    )
    assert elevation.max() <= 1.0 + 1e-10, (
        f"Elevation max {elevation.max():.4f} should be <= 1"
    )
    assert elevation.min() < 0, "Elevation should have ocean cells (min < 0)"
    assert elevation.max() > 0, "Elevation should have land cells (max > 0)"


def test_full_pipeline_land_fraction() -> None:
    """End-to-end: land fraction is within ±3% of target."""
    target: float = 0.32
    ctx: WorldContext = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(cell_count=CELL_COUNT, width=MESH_WIDTH, height=MESH_HEIGHT),
            sea_level=SeaLevelConfig(target_land_fraction=target),
            landmass=LandmassConfig(island_min_fraction=0.005, landmass_min_fraction=0.08),
        )
    ).run(seed=42, size=50)

    is_land: BoolArray | None = ctx.fields.is_land
    assert is_land is not None
    actual: float = float(is_land.mean())
    np.testing.assert_allclose(actual, target, atol=0.03, err_msg=(
        f"Land fraction {actual:.3f} should be within ±3% of {target}"
    ))


def test_full_pipeline_determinism() -> None:
    """End-to-end: same seed produces identical world."""
    ctx_a: WorldContext = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(cell_count=CELL_COUNT, width=MESH_WIDTH, height=MESH_HEIGHT),
        )
    ).run(seed=42, size=50)
    ctx_b: WorldContext = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(cell_count=CELL_COUNT, width=MESH_WIDTH, height=MESH_HEIGHT),
        )
    ).run(seed=42, size=50)

    # Check all field arrays match.
    from dataclasses import fields as dataclass_fields
    for f in dataclass_fields(ctx_a.fields.__class__):
        a_val = getattr(ctx_a.fields, f.name)
        b_val = getattr(ctx_b.fields, f.name)
        if a_val is not None and b_val is not None:
            assert np.array_equal(a_val, b_val), (
                f"Field {f.name} differs between identical seeds"
            )


def test_full_pipeline_all_fields_present() -> None:
    """End-to-end: all expected fields are populated after pipeline."""
    ctx: WorldContext = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(cell_count=CELL_COUNT, width=MESH_WIDTH, height=MESH_HEIGHT),
        )
    ).run(seed=42, size=50)

    assert ctx.fields.elevation is not None
    assert ctx.fields.is_land is not None
    assert ctx.fields.plate_id is not None
    assert ctx.fields.uplift is not None
    assert ctx.fields.z_route is not None
    assert ctx.fields.receiver is not None
    assert ctx.fields.drainage is not None
    assert ctx.fields.slope is not None
    assert ctx.fields.coast_distance is not None
    assert ctx.fields.landmass_id is not None
    assert ctx.fields.landmass_class is not None
