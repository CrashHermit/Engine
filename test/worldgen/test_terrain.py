"""Terrain contract: elevation range, sea at 0, land fraction, downhill, no NaN."""

import numpy as np
import pytest

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline

FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=500))
FAST_SIZE: int = 40
SEEDS: list[int] = [1, 7, 42]


def _debug(seed: int):
    """Run the pipeline and return (world, ctx)."""
    return WorldgenPipeline(FAST_CONFIG).run_debug(seed=seed, size=FAST_SIZE)


@pytest.mark.parametrize("seed", SEEDS)
def test_elevation_contract(seed: int) -> None:
    """Elevation is normalized to [-1, 1] with sea level pinned at 0."""
    world, _ctx = _debug(seed)
    elevation = world.grid.elevation
    assert float(elevation.min()) >= -1.0
    assert float(elevation.max()) <= 1.0
    # Sea level is at exactly 0: ocean below, land above.
    assert float(elevation.min()) < 0.0 < float(elevation.max())


@pytest.mark.parametrize("seed", SEEDS)
def test_land_fraction_near_target(seed: int) -> None:
    """Realized land fraction tracks the configured target within tolerance."""
    world, _ctx = _debug(seed)
    target = world.config.sea_level.target_land_fraction
    land_fraction = float(np.mean(world.grid.is_land))
    assert abs(land_fraction - target) < 0.1, (
        f"land fraction {land_fraction:.3f} far from target {target:.3f}"
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_land_above_sea_ocean_below(seed: int) -> None:
    """is_land agrees with the sign of elevation at sea level 0."""
    world, _ctx = _debug(seed)
    grid = world.grid
    assert np.all(grid.elevation[grid.is_land] >= 0.0)
    assert np.all(grid.elevation[~grid.is_land] < 0.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_receivers_are_downhill(seed: int) -> None:
    """Every non-pit cell routes to a strictly lower z_route (no flat cycles)."""
    _world, ctx = _debug(seed)
    receiver = ctx.fields.receiver
    z_route = ctx.fields.z_route
    has_receiver = receiver >= 0
    idx = np.flatnonzero(has_receiver)
    assert np.all(z_route[receiver[idx]] < z_route[idx]), "flow must go downhill"


@pytest.mark.parametrize("seed", SEEDS)
def test_no_nan_in_fields(seed: int) -> None:
    """No float field carries NaN or inf — the cheap catch-all."""
    world, _ctx = _debug(seed)
    grid = world.grid
    from dataclasses import fields as dataclass_fields

    for f in dataclass_fields(grid):
        value = getattr(grid, f.name)
        if value is not None and np.issubdtype(value.dtype, np.floating):
            assert np.all(np.isfinite(value)), f"{f.name} contains NaN/inf"
