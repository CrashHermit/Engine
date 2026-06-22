"""Phase 4 invariants: savagery range, leyline web, biome agreement, determinism."""

import numpy as np
import pytest

from src.core.model.environment.climate.precipitation import ORDER as PRECIP_ORDER
from src.core.model.environment.ecology.biome import BIOME_GRID
from src.core.model.environment.shared.temperature import ORDER as TEMP_ORDER
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.ecology.biomes import derive_centers
from src.worldgen.magic.web import _find, _union
from src.worldgen.pipeline import WorldgenPipeline

SEEDS = [1, 7, 42]
FAST_CONFIG: WorldgenConfig = WorldgenConfig(mesh=MeshConfig(cell_count=1500))
FAST_SIZE = 48


def _run(seed: int):
    """Run the pipeline once and return the context."""
    return WorldgenPipeline(FAST_CONFIG).run(seed=seed, size=FAST_SIZE)


# ---------------------------------------------------------------------------
# Step 1 — Savagery
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_savagery_in_unit_range(seed: int) -> None:
    """Savagery is a clipped blend: every cell lands in [0, 1]."""
    ctx = _run(seed)
    savagery = ctx.fields.savagery
    assert float(savagery.min()) >= 0.0
    assert float(savagery.max()) <= 1.0


# ---------------------------------------------------------------------------
# Step 3 — The web (MST + loops)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_leyline_web_connected(seed: int) -> None:
    """The MST connects every nexus; edges index into nexus_cells."""
    ctx = _run(seed)
    network = ctx.leylines
    k = len(network.nexus_cells)
    if k <= 1:
        assert network.edges == []
        return

    # Union every edge; a spanning web leaves exactly one component.
    parent = list(range(k))
    rank = [0] * k
    for i, j in network.edges:
        assert 0 <= i < k and 0 <= j < k, "edges must index into nexus_cells"
        _union(parent, rank, i, j)
    roots = {_find(parent, i) for i in range(k)}
    assert len(roots) == 1, "leyline web is not connected"


def test_union_find_basic() -> None:
    """Union-find merges sets and answers connectivity."""
    parent = list(range(5))
    rank = [0] * 5
    assert _union(parent, rank, 0, 1) is True
    assert _union(parent, rank, 0, 1) is False  # already joined
    _union(parent, rank, 2, 3)
    assert _find(parent, 1) == _find(parent, 0)
    assert _find(parent, 2) != _find(parent, 0)


# ---------------------------------------------------------------------------
# Step 5 — Magic fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_magic_fields_ranges(seed: int) -> None:
    """Strength in [0,1], valence in [-1,1], channels are per-cell distributions."""
    ctx = _run(seed)
    f = ctx.fields
    assert float(f.magic_strength.min()) >= 0.0
    assert float(f.magic_strength.max()) <= 1.0
    assert float(f.magic_valence.min()) >= -1.0
    assert float(f.magic_valence.max()) <= 1.0

    assert f.magic_channels.shape == (ctx.geometry.n_cells, 3)
    assert np.all(f.magic_channels >= 0.0)
    row_sums = f.magic_channels.sum(axis=1)
    assert np.allclose(row_sums, 1.0)


# ---------------------------------------------------------------------------
# Step 6 — Biomes from the one true grid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_biome_rows_sum_to_one_on_land(seed: int) -> None:
    """Every dry-land cell's biome weights form a distribution; water is zeroed."""
    ctx = _run(seed)
    f = ctx.fields
    land = f.is_land & ~f.is_lake

    row_sums = f.biome_weights.sum(axis=1)
    assert np.allclose(row_sums[land], 1.0)
    assert np.allclose(row_sums[~f.is_land], 0.0)
    assert np.allclose(row_sums[f.is_lake], 0.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_argmax_biome_matches_grid(seed: int) -> None:
    """Dominant biome equals BIOME_GRID[(temp_band, precip_band)] — views agree."""
    ctx = _run(seed)
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
        assert biome_order[col] == expected, (
            f"cell {cell}: argmax {biome_order[col]} != grid {expected}"
        )


# ---------------------------------------------------------------------------
# Determinism (lots of rng entered this phase)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_phase4_deterministic(seed: int) -> None:
    """Same seed reproduces savagery, the leyline web, magic fields, and biomes."""
    ctx_a = _run(seed)
    ctx_b = _run(seed)
    fa, fb = ctx_a.fields, ctx_b.fields

    assert np.array_equal(fa.savagery, fb.savagery)
    assert np.array_equal(fa.magic_strength, fb.magic_strength)
    assert np.array_equal(fa.magic_valence, fb.magic_valence)
    assert np.array_equal(fa.magic_channels, fb.magic_channels)
    assert np.array_equal(fa.biome_weights, fb.biome_weights)

    assert ctx_a.leylines.nexus_cells == ctx_b.leylines.nexus_cells
    assert ctx_a.leylines.edges == ctx_b.leylines.edges
    assert np.array_equal(
        ctx_a.leylines.nexus_valence, ctx_b.leylines.nexus_valence
    )
