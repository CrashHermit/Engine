"""Tests for lake extraction (Phase 3 step 4)."""

import numpy as np

from src.worldgen.config.worldgen_config import LakeConfig
from src.core.model.environment.water.lake import Lake
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.water.lakes import extract_lakes


def _make_geometry(
    sites: list[tuple[float, float]],
    width: float = 1.0,
    height: float = 1.0,
) -> tuple[int, list[list[int]]]:
    """Build a minimal (n, adjacency_list) geometry from site coordinates.

    Two cells are neighbors if their torus distance is below the median
    pairwise distance.  Returns (n, adj) where adj[i] is a list of
    neighbour cell ids.
    """
    n: int = len(sites)
    dists: list[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            d: float = torus_distance(
                a=np.array(sites[i]),
                b=np.array(sites[j]),
                width=width,
                height=height,
            )
            dists.append(d)

    if not dists:
        return n, [[] for _ in range(n)]

    threshold: float = float(np.median(dists))

    adj: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = torus_distance(
                a=np.array(sites[i]),
                b=np.array(sites[j]),
                width=width,
                height=height,
            )
            if d <= threshold:
                adj[i].append(j)
                adj[j].append(i)

    return n, adj


def _mock_geometry(n: int, adj: list[list[int]]):
    """Return a lightweight object that mimics MeshGeometry.neighbors_of."""

    class _G:
        n_cells = n

        def neighbors_of(self, *, cell_id: int) -> list[int]:
            return adj[cell_id]

    return _G()


def test_empty_mesh():
    """No lake cells when the mesh is empty."""
    n = 0
    z = np.zeros(0, dtype=np.float64)
    z_route = np.zeros(0, dtype=np.float64)
    is_land = np.zeros(0, dtype=bool)
    cfg = LakeConfig()
    geom = _mock_geometry(n, [])

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert lakes == []
    assert len(lake_id) == 0
    assert len(is_lake) == 0


def test_single_lake():
    """A single connected depression produces one lake."""
    # 9 cells: a 3x3 grid where the center cell is a depression.
    sites = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
        (0.0, 1.0), (0.5, 1.0), (1.0, 1.0),
    ]
    n, adj = _make_geometry(sites, width=1.0, height=1.0)
    geom = _mock_geometry(n, adj)

    # All cells at elevation 0.5 except center (cell 4) at 0.0.
    z = np.full(n, 0.5, dtype=np.float64)
    z[4] = 0.0
    # z_route is same as z except center where it's slightly higher.
    z_route = z.copy()
    z_route[4] = 0.3

    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 1
    assert isinstance(lakes[0], Lake)
    assert lakes[0].id == 0
    assert len(lakes[0].cells) == 1
    assert lakes[0].cells[0] == 4
    assert abs(lakes[0].surface_level - 0.3) < 1e-9
    # Center cell has no outside neighbor with lower z_route (all neighbors
    # are at z_route=0.5 > 0.3), so it's terminal.
    assert lakes[0].outlet_cell is None

    # Only cell 4 is marked as a lake.
    assert is_lake[4]
    assert int(np.sum(is_lake)) == 1


def test_multiple_lakes():
    """Two separate depressions produce two lakes."""
    # 6 cells in a line: 0-1-2-3-4-5. Cell 1 and cell 4 are depressions.
    # They are separated by cell 2 and 3 which are NOT depressions.
    sites = [
        (0.0, 0.0), (1.0, 0.0), (2.0, 0.0),
        (3.0, 0.0), (4.0, 0.0), (5.0, 0.0),
    ]
    n, adj = _make_geometry(sites, width=6.0, height=1.0)
    geom = _mock_geometry(n, adj)

    # All cells at elevation 0.0 (flat terrain).
    z = np.zeros(n, dtype=np.float64)
    # Two depressions: cell 1 and cell 4.
    z_route = z.copy()
    z_route[1] = 0.3  # water surface above terrain
    z_route[4] = 0.4  # water surface above terrain

    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 2
    lake_ids = {l.id for l in lakes}
    assert 0 in lake_ids and 1 in lake_ids

    # Each lake should have exactly 1 cell.
    for lake in lakes:
        assert len(lake.cells) == 1
        assert is_lake[lake.cells[0]]

    # Verify all non-lake cells are False.
    for i in range(n):
        if i not in (1, 4):
            assert not is_lake[i]


def test_multi_cell_lake_is_one_component():
    """A connected chain of depression cells is a single lake.

    Guards the BFS: every cell reachable through the lake mask must land in
    the same component, not just the seed's immediate neighbors.
    """
    # 5 cells in a line, each adjacent to the next; all are lake cells.
    n = 5
    adj = [[1], [0, 2], [1, 3], [2, 4], [3]]
    geom = _mock_geometry(n, adj)

    z = np.zeros(n, dtype=np.float64)
    z_route = np.full(n, 0.5, dtype=np.float64)  # whole chain is one filled basin
    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 1
    assert sorted(lakes[0].cells) == [0, 1, 2, 3, 4]
    assert bool(np.all(is_lake))
    assert bool(np.all(lake_id == 0))


def test_lake_with_outlet():
    """A depression connected to a lower outside cell has an outlet."""
    # 7 cells: 1-2-3-4-5-6-7 in a line, cell 3 is a depression,
    # cell 7 has a very low z_route (the ocean).
    sites = [
        (i, 0.0) for i in range(7)
    ]
    n, adj = _make_geometry(sites, width=7.0, height=1.0)
    geom = _mock_geometry(n, adj)

    # All cells at elevation 0.0 (flat terrain).
    z = np.zeros(n, dtype=np.float64)
    z_route = np.zeros(n, dtype=np.float64)

    # Cell 3 is a depression: water surface (0.6) is above terrain (0.0)
    # and above neighbors' surface (0.5), so it spills outward.
    z[3] = 0.0
    z_route[3] = 0.6

    # Cell 6 and 7 connect to cell 3. Cell 7 has lower z_route.
    # The outlet should be cell 3 (boundary cell whose neighbor 6 or 7
    # has the lowest z_route).
    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 1
    assert lakes[0].outlet_cell is not None
    # The outlet should be cell 3 (it's the boundary cell with the
    # lowest outside neighbor z_route).
    assert lakes[0].outlet_cell == 3


def test_ocean_cells_not_lakes():
    """Ocean cells (is_land=False) are never marked as lakes."""
    sites = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
    ]
    n, adj = _make_geometry(sites, width=1.0, height=1.0)
    geom = _mock_geometry(n, adj)

    z = np.full(n, 0.0, dtype=np.float64)
    z_route = z.copy()
    z_route[0] = 0.1  # Would look like a lake if not for is_land

    # Cell 0 is ocean (is_land=False).
    is_land = np.zeros(n, dtype=bool)
    is_land[1:] = True
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 0
    assert not is_lake[0]


def test_lake_mask_epsilon():
    """Cells where z_route == z + epsilon are not lakes (epsilon guard)."""
    sites = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
    ]
    n, adj = _make_geometry(sites, width=1.0, height=1.0)
    geom = _mock_geometry(n, adj)

    z = np.full(n, 0.5, dtype=np.float64)
    # z_route is exactly z + epsilon — should NOT be a lake.
    epsilon = 1e-6
    z_route = z.copy()
    z_route[0] = z[0] + epsilon  # Exactly at threshold

    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=epsilon)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    # z_route > z + epsilon is False when z_route == z + epsilon.
    assert len(lakes) == 0
    assert not is_lake[0]


def test_lake_mask_epsilon_above():
    """Cells where z_route > z + epsilon ARE lakes."""
    sites = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
    ]
    n, adj = _make_geometry(sites, width=1.0, height=1.0)
    geom = _mock_geometry(n, adj)

    z = np.full(n, 0.5, dtype=np.float64)
    # z_route is z + 2*epsilon — should be a lake.
    epsilon = 1e-6
    z_route = z.copy()
    z_route[0] = z[0] + 2 * epsilon

    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=epsilon)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 1
    assert lakes[0].cells[0] == 0
    assert is_lake[0]


def test_lake_id_consistency():
    """lake_id values match lake ids and is_lake mask."""
    sites = [
        (0.0, 0.0), (0.3, 0.0), (0.6, 0.0), (0.9, 0.0),
        (0.0, 0.5), (0.3, 0.5), (0.6, 0.5), (0.9, 0.5),
    ]
    n, adj = _make_geometry(sites, width=1.0, height=1.0)
    geom = _mock_geometry(n, adj)

    z = np.full(n, 0.5, dtype=np.float64)
    z_route = z.copy()
    z_route[1] = 0.3
    z_route[5] = 0.4

    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    # lake_id >= 0 iff is_lake
    assert np.array_equal(lake_id >= 0, is_lake)

    # Each lake cell has lake_id matching the lake's id.
    for lake in lakes:
        for cell_id in lake.cells:
            assert lake_id[cell_id] == lake.id

    # Non-lake cells have lake_id == -1.
    for i in range(n):
        if not is_lake[i]:
            assert lake_id[i] == -1


def test_lake_surface_level():
    """Lake surface_level equals z_route of its cells."""
    sites = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
    ]
    n, adj = _make_geometry(sites, width=1.0, height=1.0)
    geom = _mock_geometry(n, adj)

    z = np.full(n, 0.5, dtype=np.float64)
    expected_surface = 0.75
    z_route = z.copy()
    z_route[2] = expected_surface

    is_land = np.ones(n, dtype=bool)
    cfg = LakeConfig(epsilon=1e-6)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_route, is_land=is_land, cfg=cfg,
        discharge=np.full(n, 1e9), evaporation=np.zeros(n),
    )

    assert len(lakes) == 1
    assert abs(lakes[0].surface_level - expected_surface) < 1e-9


# ---------------------------------------------------------------------------
# Water balance: inflow vs evaporation decides how far a depression fills.
# ---------------------------------------------------------------------------


def _bowl():
    """A 3-cell bowl in a line: z = [0.0, 0.1, 0.2], spill at 0.3."""
    n = 3
    adj = [[1], [0, 2], [1]]
    geom = _mock_geometry(n, adj)
    z = np.array([0.0, 0.1, 0.2], dtype=np.float64)
    z_filled = np.full(n, 0.3, dtype=np.float64)  # filled to spill
    is_land = np.ones(n, dtype=bool)
    return n, geom, z, z_filled, is_land


def test_partial_lake_is_endorheic():
    """Inflow that covers only the lowest cells yields a partial, endorheic lake."""
    n, geom, z, z_filled, is_land = _bowl()
    cfg = LakeConfig(epsilon=1e-6)
    # evaporation 1/cell, inflow 1.5: cell 0 submerges (cum 1.0), cell 1 would
    # tip to 2.0 > 1.5, so the lake equilibrates at cell 1's rim.
    evaporation = np.ones(n, dtype=np.float64)
    discharge = np.full(n, 1.5, dtype=np.float64)

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_filled, is_land=is_land, cfg=cfg,
        discharge=discharge, evaporation=evaporation,
    )

    assert len(lakes) == 1
    assert lakes[0].cells == [0]
    assert lakes[0].endorheic is True
    assert lakes[0].outlet_cell is None
    assert abs(lakes[0].surface_level - 0.1) < 1e-9
    assert is_lake[0] and not is_lake[1] and not is_lake[2]


def test_arid_basin_stays_dry():
    """When evaporation outstrips inflow even at the pit, no lake forms."""
    n, geom, z, z_filled, is_land = _bowl()
    cfg = LakeConfig(epsilon=1e-6)
    evaporation = np.ones(n, dtype=np.float64)
    discharge = np.full(n, 0.5, dtype=np.float64)  # below the pit's own evaporation

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_filled, is_land=is_land, cfg=cfg,
        discharge=discharge, evaporation=evaporation,
    )

    assert lakes == []
    assert not np.any(is_lake)


def test_wet_basin_brims_and_overflows():
    """Inflow exceeding whole-pool evaporation fills to the spill (exorheic)."""
    n, geom, z, z_filled, is_land = _bowl()
    cfg = LakeConfig(epsilon=1e-6)
    evaporation = np.ones(n, dtype=np.float64)
    discharge = np.full(n, 5.0, dtype=np.float64)  # outlasts 3.0 total evaporation

    lakes, lake_id, is_lake = extract_lakes(
        geometry=geom, z=z, z_filled=z_filled, is_land=is_land, cfg=cfg,
        discharge=discharge, evaporation=evaporation,
    )

    assert len(lakes) == 1
    assert sorted(lakes[0].cells) == [0, 1, 2]
    assert lakes[0].endorheic is False
    assert abs(lakes[0].surface_level - 0.3) < 1e-9
    assert bool(np.all(is_lake))
