"""Ocean-current (sea-surface temperature) sanity suite.

Two tiers, per ``docs/worldgen-ocean-currents-plan.md`` §7:

* **Hard invariants** — range, bounded/no-runaway, perturb-not-erase, land =
  baseline, determinism.
* **Toroidal-signature bands** — currents are not a no-op; an all-ocean band
  homogenizes zonally (circumpolar current); meridional flow warms downstream;
  the no-normal-flow boundary condition deflects wind off coasts.

The signature tests run on synthetic meshes (controlled, fast, deterministic)
so they don't depend on a random world happening to grow an all-ocean band; the
invariants additionally run against full pipeline worlds.
"""

from dataclasses import replace

import numpy as np
import pytest

from src.worldgen.climate.ocean_current import (
    _coast_projected_wind,
    compute_sst,
    maritime_sst_onshore,
)
from src.worldgen.config import presets as P
from src.worldgen.config.worldgen_config import (
    MeshConfig,
    OceanCurrentConfig,
    WorldgenConfig,
)
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.pipeline import WorldgenPipeline


# ---------------------------------------------------------------------------
# Synthetic-mesh helpers
# ---------------------------------------------------------------------------


def _mesh(n: int = 800, size: int = 60) -> MeshGeometry:
    return build_mesh(
        seed=1, cell_count=n, lloyd_iterations=1, width=float(size), height=float(size)
    )


def _y_banded_baseline(geometry: MeshGeometry) -> np.ndarray:
    """A latitude-like baseline in [0, 1] that depends only on torus-y (wraps)."""
    y = geometry.sites[:, 1]
    return 0.5 + 0.5 * np.cos(2.0 * np.pi * y / geometry.height)


# ---------------------------------------------------------------------------
# Signature: circumpolar homogenization
# ---------------------------------------------------------------------------


def test_all_ocean_zonal_band_homogenizes() -> None:
    """A pure-zonal current over an all-ocean, y-banded sea is uniform *across x*.

    Advecting a field that is constant along x with an eastward wind carries each
    cell's heat to a same-latitude neighbor, so within any latitude band SST is
    nearly constant around the torus — the circumpolar-current signature.  (The
    band *mean* may drift slightly from baseline through meridional mixing; what
    must stay tiny is the *zonal* variance within a band.)
    """
    g = _mesh()
    n = g.n_cells
    baseline = _y_banded_baseline(g)
    is_land = np.zeros(n, dtype=bool)

    sst = compute_sst(
        geometry=g,
        wind_u=np.ones(n),
        wind_v=np.zeros(n),
        insolation=baseline,
        is_land=is_land,
        cfg=OceanCurrentConfig(),
    )
    # Within latitude bands, SST varies across x no more than the baseline
    # itself does (which is purely meridional): the current adds no zonal
    # structure of its own.
    y = g.sites[:, 1]
    bands = np.floor(y / g.height * 16).astype(int)
    labels = [b for b in np.unique(bands) if np.sum(bands == b) > 3]
    sst_zonal = max(float(sst[bands == b].std()) for b in labels)
    base_zonal = max(float(baseline[bands == b].std()) for b in labels)
    assert sst_zonal <= base_zonal + 0.012, (
        f"current manufactured zonal variance: sst {sst_zonal:.3f} vs baseline {base_zonal:.3f}"
    )


# ---------------------------------------------------------------------------
# Signature: meridional current warms/cools downstream
# ---------------------------------------------------------------------------


def test_meridional_current_creates_anomalies() -> None:
    """Flow across the latitude gradient carries warmth/cold: nonzero anomalies."""
    g = _mesh()
    n = g.n_cells
    baseline = _y_banded_baseline(g)
    is_land = np.zeros(n, dtype=bool)
    wind_u = np.zeros(n)
    wind_v = np.ones(n)  # poleward/equatorward flow across the y gradient

    sst = compute_sst(
        geometry=g,
        wind_u=wind_u,
        wind_v=wind_v,
        insolation=baseline,
        is_land=is_land,
        cfg=OceanCurrentConfig(),
    )
    anomaly = sst - baseline
    # Both a warm side (carrying warm water into cold latitudes) and a cold side.
    assert anomaly.max() > 0.03, "no warm current produced"
    assert anomaly.min() < -0.03, "no cold current produced"
    # Bounded by the baseline extremes (convex blend → no runaway).
    assert sst.min() >= baseline.min() - 1e-9
    assert sst.max() <= baseline.max() + 1e-9


# ---------------------------------------------------------------------------
# Signature: no-normal-flow boundary condition
# ---------------------------------------------------------------------------


def test_coastal_boundary_condition_deflects_wind() -> None:
    """Wind blowing into a coast loses its onshore component (deflects alongshore)."""
    g = _mesh()
    n = g.n_cells
    y = g.sites[:, 1]
    is_land = y > g.height / 2.0  # a land band; wind below blows up into it
    wind_u = np.zeros(n)
    wind_v = np.ones(n)  # +y, straight at the coast

    eff_u, eff_v = _coast_projected_wind(
        geometry=g, wind_u=wind_u, wind_v=wind_v, is_land=is_land
    )

    # Coastal ocean cells: those with at least one land neighbor.
    coastal = np.array(
        [
            (not is_land[i])
            and any(bool(is_land[int(j)]) for j in g.neighbors_of(cell_id=i))
            for i in range(n)
        ]
    )
    assert coastal.any()
    # The onshore (+y) component is reduced where the wind hit the coast.
    assert eff_v[coastal].mean() < wind_v[coastal].mean() - 1e-6
    # Interior ocean (no land neighbor) keeps its wind untouched.
    interior = (~is_land) & ~coastal
    assert np.allclose(eff_v[interior], 1.0)


# ---------------------------------------------------------------------------
# Invariant: maritime SST carries ocean values onshore
# ---------------------------------------------------------------------------


def test_maritime_sst_matches_ocean_and_warms_coast() -> None:
    """Onshore SST equals the ocean SST over water and stays in range on land."""
    g = _mesh()
    n = g.n_cells
    y = g.sites[:, 1]
    is_land = y > g.height / 2.0
    baseline = _y_banded_baseline(g)
    sst = baseline.copy()
    sst[~is_land] = np.clip(sst[~is_land] + 0.2, 0.0, 1.0)  # a warm sea

    maritime = maritime_sst_onshore(
        geometry=g,
        wind_u=np.zeros(n),
        wind_v=-np.ones(n),  # blow from the (warm) ocean onto the land band
        sst=sst,
        insolation=baseline,
        is_land=is_land,
        reach=4.0,
    )
    assert np.allclose(maritime[~is_land], sst[~is_land])  # ocean unchanged
    assert maritime.min() >= 0.0 and maritime.max() <= 1.0


# ---------------------------------------------------------------------------
# Pipeline integration — invariants on real worlds
# ---------------------------------------------------------------------------

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


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_sst_range_and_land_is_baseline(preset: str, seed: int) -> None:
    _world_data, ctx = _world(preset, seed)
    sst = ctx.fields.sst
    ins = ctx.fields.insolation
    land = ctx.fields.is_land
    ocean = ~land
    assert sst[ocean].min() >= 0.0 and sst[ocean].max() <= 1.0
    # Land carries its own radiative baseline (no sea there).
    assert np.allclose(sst[land], ins[land])
    # Bounded by baseline extremes — no runaway warming.
    assert sst[ocean].min() >= ins.min() - 1e-9
    assert sst[ocean].max() <= ins.max() + 1e-9


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_perturb_not_erase(preset: str, seed: int) -> None:
    """Currents nudge the latitude gradient but never invert its global sign."""
    _world_data, ctx = _world(preset, seed)
    sst = ctx.fields.sst
    lat = np.abs(ctx.fields.latitude)
    ocean = ~ctx.fields.is_land
    equatorial = ocean & (lat < 0.25)
    polar = ocean & (lat > 0.75)
    assert equatorial.any() and polar.any()
    assert sst[equatorial].mean() > sst[polar].mean(), "latitude gradient erased"


@pytest.mark.parametrize(("preset", "seed"), CASES)
def test_currents_are_not_a_noop(preset: str, seed: int) -> None:
    """The current measurably departs from the latitude baseline somewhere."""
    _world_data, ctx = _world(preset, seed)
    anomaly = ctx.fields.sst - ctx.fields.insolation
    ocean = ~ctx.fields.is_land
    assert np.max(np.abs(anomaly[ocean])) > 0.03, "currents do nothing"


def test_determinism() -> None:
    cfg = replace(P.earthlike(), mesh=MeshConfig(cell_count=_CELLS))
    a, _ = WorldgenPipeline(cfg).run_debug(seed=3, size=_SIZE)
    b, _ = WorldgenPipeline(cfg).run_debug(seed=3, size=_SIZE)
    assert np.array_equal(a.grid.sst, b.grid.sst)
