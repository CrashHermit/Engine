"""Climate invariants: field ranges, causality, unit-length wind, determinism."""

import numpy as np
import pytest

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.types import BoolArray, Float64Array

CELL_COUNT: int = 2000
MESH_WIDTH: float = 50.0
MESH_HEIGHT: float = 50.0
PIPELINE_SIZE: int = 40


# ---------------------------------------------------------------------------
# Range tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_temperature_and_precip_in_unit_range(seed: int) -> None:
    """Climate fields stay in [0, 1]."""
    ctx = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=seed, size=PIPELINE_SIZE)

    temperature: Float64Array | None = ctx.fields.temperature
    assert temperature is not None
    assert float(temperature.min()) >= 0.0, (
        f"temperature min {temperature.min():.4f} should be >= 0"
    )
    assert float(temperature.max()) <= 1.0, (
        f"temperature max {temperature.max():.4f} should be <= 1"
    )

    precipitation: Float64Array | None = ctx.fields.precipitation
    assert precipitation is not None
    assert float(precipitation.min()) >= 0.0, (
        f"precipitation min {precipitation.min():.4f} should be >= 0"
    )
    assert float(precipitation.max()) <= 1.0, (
        f"precipitation max {precipitation.max():.4f} should be <= 1"
    )


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_wind_magnitude_in_unit_range(seed: int) -> None:
    """Wind magnitude stays in [0, 1]."""
    ctx = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=seed, size=PIPELINE_SIZE)

    mag: Float64Array | None = ctx.fields.wind_magnitude
    assert mag is not None
    assert float(mag.min()) >= 0.0, (
        f"wind_magnitude min {mag.min():.4f} should be >= 0"
    )
    assert float(mag.max()) <= 1.0 + 1e-9, (
        f"wind_magnitude max {mag.max():.4f} should be <= 1"
    )


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_wind_direction_unit_length(seed: int) -> None:
    """(wind_u, wind_v) is unit-length wherever wind_magnitude > 0."""
    ctx = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=seed, size=PIPELINE_SIZE)

    u: Float64Array | None = ctx.fields.wind_u
    v: Float64Array | None = ctx.fields.wind_v
    mag: Float64Array | None = ctx.fields.wind_magnitude
    assert u is not None
    assert v is not None
    assert mag is not None

    active: BoolArray = mag > 1e-6
    assert int(active.sum()) > 0, "Expected some active wind cells"

    length: Float64Array = np.sqrt(u[active] ** 2 + v[active] ** 2)
    expected: float = 1.0
    np.testing.assert_allclose(
        actual=float(length.mean()),
        desired=expected,
        atol=1e-5,
        err_msg=(
            f"Wind direction length {length.mean():.6f} "
            f"should be 1.0 where magnitude > 0"
        ),
    )


# ---------------------------------------------------------------------------
# Causality smoke test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_coasts_wetter_than_interiors(seed: int) -> None:
    """Transport loop carries ocean moisture inland and spends it (sign check)."""
    ctx = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=seed, size=PIPELINE_SIZE)

    precipitation: Float64Array | None = ctx.fields.precipitation
    coast_distance: Float64Array | None = ctx.fields.coast_distance
    is_land: BoolArray | None = ctx.fields.is_land
    assert precipitation is not None
    assert coast_distance is not None
    assert is_land is not None

    land: BoolArray = is_land

    # Compare bottom quartile (coastal) vs top quartile (inland) of coast_distance.
    land_coast: Float64Array = coast_distance[land]
    threshold: float = float(np.percentile(land_coast, 50))

    near_coast: BoolArray = (coast_distance < threshold) & land
    far_inland: BoolArray = (coast_distance >= threshold) & land

    assert int(near_coast.sum()) > 0, (
        f"Expected land cells with coast_distance < {threshold:.1f}"
    )
    assert int(far_inland.sum()) > 0, (
        f"Expected land cells with coast_distance >= {threshold:.1f}"
    )

    near_precip_mean: float = float(precipitation[near_coast].mean())
    far_precip_mean: float = float(precipitation[far_inland].mean())

    assert near_precip_mean > far_precip_mean, (
        f"Coastal precip ({near_precip_mean:.4f}) should exceed "
        f"inland precip ({far_precip_mean:.4f})"
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_climate_determinism() -> None:
    """Same seed produces identical climate fields."""
    ctx_a = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=42, size=PIPELINE_SIZE)
    ctx_b = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=42, size=PIPELINE_SIZE)

    climate_fields: list[str] = [
        "temperature",
        "precipitation",
        "wind_u",
        "wind_v",
        "wind_magnitude",
    ]

    for field_name in climate_fields:
        a_val = getattr(ctx_a.fields, field_name)
        b_val = getattr(ctx_b.fields, field_name)
        assert a_val is not None and b_val is not None
        assert np.array_equal(a_val, b_val), (
            f"Climate field {field_name} differs between identical seeds"
        )


# ---------------------------------------------------------------------------
# Field presence
# ---------------------------------------------------------------------------


def test_all_climate_fields_present() -> None:
    """All climate fields are populated after pipeline."""
    ctx = WorldgenPipeline(
        WorldgenConfig(
            mesh=MeshConfig(
                cell_count=CELL_COUNT,
                width=MESH_WIDTH,
                height=MESH_HEIGHT,
            ),
        )
    ).run(seed=42, size=PIPELINE_SIZE)

    assert ctx.fields.insolation is not None
    assert ctx.fields.temperature is not None
    assert ctx.fields.precipitation is not None
    assert ctx.fields.wind_u is not None
    assert ctx.fields.wind_v is not None
    assert ctx.fields.wind_magnitude is not None
