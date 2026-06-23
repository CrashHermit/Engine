"""Climate, magic, and ecology invariants: field ranges, causality, agreement.

Consolidates the former ``test_climate`` and ``test_magic_ecology`` suites.
Determinism for these fields lives in ``test_determinism`` (whole-WorldData).
"""

import numpy as np
import pytest

from src.core.model.environment.climate.precipitation import ORDER as PRECIP_ORDER
from src.core.model.environment.ecology.biome import BIOME_GRID
from src.core.model.environment.shared.temperature import ORDER as TEMP_ORDER
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.ecology.biomes import derive_centers
from src.worldgen.magic.web import _find, _union
from src.worldgen.pipeline import WorldgenPipeline

# Climate causality (coasts wetter than interiors) needs landmasses big enough
# to *have* interiors, so this suite uses a slightly larger mesh than the others.
FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=1500))
FAST_SIZE: int = 40
SEEDS: list[int] = [1, 7, 42]

_WORLD_CACHE: dict[int, tuple] = {}


def _debug(seed: int):
    """Run the pipeline once per seed (cached) and return (world, ctx)."""
    if seed not in _WORLD_CACHE:
        _WORLD_CACHE[seed] = WorldgenPipeline(FAST_CONFIG).run_debug(
            seed=seed, size=FAST_SIZE
        )
    return _WORLD_CACHE[seed]


# ---------------------------------------------------------------------------
# Climate field ranges and causality
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_climate_fields_in_unit_range(seed: int) -> None:
    """Temperature, precipitation, and wind magnitude stay in [0, 1]."""
    _world, ctx = _debug(seed)
    for name in ("temperature", "precipitation", "wind_magnitude"):
        values = getattr(ctx.fields, name)
        assert values is not None
        assert float(values.min()) >= 0.0
        assert float(values.max()) <= 1.0 + 1e-9, name


@pytest.mark.parametrize("seed", SEEDS)
def test_wind_direction_unit_length(seed: int) -> None:
    """(wind_u, wind_v) is unit-length wherever wind_magnitude > 0."""
    _world, ctx = _debug(seed)
    u, v, mag = ctx.fields.wind_u, ctx.fields.wind_v, ctx.fields.wind_magnitude
    active = mag > 1e-6
    assert int(active.sum()) > 0
    length = np.sqrt(u[active] ** 2 + v[active] ** 2)
    np.testing.assert_allclose(float(length.mean()), 1.0, atol=1e-5)


@pytest.mark.parametrize("seed", SEEDS)
def test_coasts_wetter_than_interiors(seed: int) -> None:
    """Ocean moisture advected inland leaves coasts wetter than deep interiors."""
    _world, ctx = _debug(seed)
    precip = ctx.fields.precipitation
    coast = ctx.fields.coast_distance
    land = ctx.fields.is_land

    land_coast = coast[land]
    if float(land_coast.max()) < 2.0:
        pytest.skip("world has no real interior at this resolution")

    threshold = float(np.percentile(land_coast, 50))
    near = (coast < threshold) & land
    far = (coast >= threshold) & land
    assert int(near.sum()) > 0 and int(far.sum()) > 0
    assert float(precip[near].mean()) > float(precip[far].mean())


@pytest.mark.parametrize("seed", SEEDS)
def test_all_climate_fields_present(seed: int) -> None:
    """Every climate field is populated after the pipeline runs."""
    _world, ctx = _debug(seed)
    for name in (
        "insolation",
        "temperature",
        "precipitation",
        "wind_u",
        "wind_v",
        "wind_magnitude",
    ):
        assert getattr(ctx.fields, name) is not None


# ---------------------------------------------------------------------------
# Magic: savagery, the web, and the rasterized fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_savagery_in_unit_range(seed: int) -> None:
    """Savagery is a clipped blend: every cell lands in [0, 1]."""
    _world, ctx = _debug(seed)
    savagery = ctx.fields.savagery
    assert float(savagery.min()) >= 0.0
    assert float(savagery.max()) <= 1.0


@pytest.mark.parametrize("seed", SEEDS)
def test_leyline_web_connected(seed: int) -> None:
    """The MST connects every nexus; edges index into nexus_cells."""
    _world, ctx = _debug(seed)
    network = ctx.leylines
    k = len(network.nexus_cells)
    if k <= 1:
        assert network.edges == []
        return

    parent = list(range(k))
    rank = [0] * k
    for i, j in network.edges:
        assert 0 <= i < k and 0 <= j < k
        _union(parent, rank, i, j)
    roots = {_find(parent, i) for i in range(k)}
    assert len(roots) == 1, "leyline web is not connected"


def test_union_find_basic() -> None:
    """Union-find merges sets and answers connectivity."""
    parent = list(range(5))
    rank = [0] * 5
    assert _union(parent, rank, 0, 1) is True
    assert _union(parent, rank, 0, 1) is False
    _union(parent, rank, 2, 3)
    assert _find(parent, 1) == _find(parent, 0)
    assert _find(parent, 2) != _find(parent, 0)


@pytest.mark.parametrize("seed", SEEDS)
def test_magic_fields_ranges(seed: int) -> None:
    """Strength in [0,1], valence in [-1,1], channels are per-cell distributions."""
    _world, ctx = _debug(seed)
    f = ctx.fields
    assert float(f.magic_strength.min()) >= 0.0
    assert float(f.magic_strength.max()) <= 1.0
    assert float(f.magic_valence.min()) >= -1.0
    assert float(f.magic_valence.max()) <= 1.0

    assert f.magic_channels.shape == (ctx.geometry.n_cells, 3)
    assert np.all(f.magic_channels >= 0.0)
    np.testing.assert_allclose(f.magic_channels.sum(axis=1), 1.0)


# ---------------------------------------------------------------------------
# Ecology: biomes from the one true grid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_biome_rows_sum_to_one_on_land(seed: int) -> None:
    """Every dry-land cell's biome weights form a distribution; water is zeroed."""
    _world, ctx = _debug(seed)
    f = ctx.fields
    land = f.is_land & ~f.is_lake
    row_sums = f.biome_weights.sum(axis=1)
    np.testing.assert_allclose(row_sums[land], 1.0)
    np.testing.assert_allclose(row_sums[~f.is_land], 0.0)
    np.testing.assert_allclose(row_sums[f.is_lake], 0.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_argmax_biome_matches_grid(seed: int) -> None:
    """Dominant biome equals BIOME_GRID[(temp_band, precip_band)] — views agree."""
    _world, ctx = _debug(seed)
    f = ctx.fields
    _ct, _cp, biome_order = derive_centers()
    n_bands = len(TEMP_ORDER)

    land = np.flatnonzero(f.is_land & ~f.is_lake)
    rng = np.random.default_rng(seed)
    sample = rng.choice(land, size=min(80, land.size), replace=False)

    for cell in sample:
        col = int(np.argmax(f.biome_weights[cell]))
        t_idx = min(int(f.temperature[cell] * n_bands), n_bands - 1)
        p_idx = min(int(f.precipitation[cell] * n_bands), n_bands - 1)
        expected = BIOME_GRID[(TEMP_ORDER[t_idx], PRECIP_ORDER[p_idx])]
        assert biome_order[col] == expected
