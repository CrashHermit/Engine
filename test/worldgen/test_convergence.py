"""Convergence-derived rain belts: the latitudinal banding emerges from wind.

Per ``docs/worldgen-convergence-rain-plan.md``: wind convergence (rising air)
rains moisture out and subsidence dries it, so the wet-equator / dry-subtropics
banding is a consequence of the prevailing wind — not an authored Gaussian.
"""

from dataclasses import replace

import numpy as np
import pytest

from src.worldgen.config import presets as P
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.geometry.mesh import build_mesh
from src.worldgen.climate.wind import convergence_field, wind_divergence
from src.worldgen.pipeline import WorldgenPipeline

_CELLS = 2500
_SIZE = 80
_CACHE: dict[tuple[str, int], tuple] = {}


def _world(preset: str, seed: int):
    key = (preset, seed)
    if key not in _CACHE:
        base: WorldgenConfig = getattr(P, preset)()
        cfg = replace(base, mesh=MeshConfig(cell_count=_CELLS))
        _CACHE[key] = WorldgenPipeline(cfg).run_debug(seed=seed, size=_SIZE)
    return _CACHE[key]


CASES = [("earthlike", 1), ("earthlike", 42), ("pangaea", 7)]


def test_divergence_of_uniform_wind_is_zero() -> None:
    """A spatially-constant wind field has no convergence anywhere."""
    g = build_mesh(seed=1, cell_count=600, lloyd_iterations=1, width=60.0, height=60.0)
    n = g.n_cells
    div = wind_divergence(
        geometry=g, vel_u=np.full(n, 0.7), vel_v=np.full(n, -0.3)
    )
    assert np.max(np.abs(div)) < 1e-9


def test_convergence_field_signed_and_bounded() -> None:
    """convergence_field is signed, in [-1, 1], and flips sign with divergence."""
    g = build_mesh(seed=2, cell_count=600, lloyd_iterations=1, width=60.0, height=60.0)
    n = g.n_cells
    # A converging flow toward the center column (u points inward in x).
    x = g.sites[:, 0]
    vel_u = np.where(x < g.width / 2, 1.0, -1.0)
    vel_v = np.zeros(n)
    div = wind_divergence(geometry=g, vel_u=vel_u, vel_v=vel_v)
    conv = convergence_field(divergence=div, percentile=90.0)
    assert conv.min() >= -1.0 and conv.max() <= 1.0
    # Some cells rise (convergence) and some sink (divergence).
    assert conv.max() > 0.0 and conv.min() < 0.0


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_convergence_range_and_determinism(preset: str, seed: int) -> None:
    _w, ctx = _world(preset, seed)
    conv = ctx.fields.convergence
    assert conv.min() >= -1.0 and conv.max() <= 1.0
    _w2, ctx2 = WorldgenPipeline(
        replace(getattr(P, preset)(), mesh=MeshConfig(cell_count=_CELLS))
    ).run_debug(seed=seed, size=_SIZE)
    assert np.array_equal(conv, ctx2.fields.convergence)


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_itcz_emerges_from_convergence(preset: str, seed: int) -> None:
    """The equatorial band converges (rises) more than the subtropics subside."""
    _w, ctx = _world(preset, seed)
    conv = ctx.fields.convergence
    lat = np.abs(ctx.fields.latitude)
    equator = conv[lat < 0.2].mean()
    subtropics = conv[(lat > 0.25) & (lat < 0.45)].mean()
    assert equator > subtropics, "equator not more convergent than subtropics"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_equator_wetter_than_subtropics(preset: str, seed: int) -> None:
    """The latitude belt makes equatorial land wetter than the subtropics."""
    world, _ctx = _world(preset, seed)
    g = world.grid
    land = g.is_land & ~g.is_lake
    lat = np.abs(g.latitude[land])
    precip = g.precipitation[land]
    eq = precip[lat < 0.2]
    sub = precip[(lat > 0.25) & (lat < 0.45)]
    if eq.size and sub.size:
        assert eq.mean() > sub.mean(), "equatorial land not wetter than subtropics"
