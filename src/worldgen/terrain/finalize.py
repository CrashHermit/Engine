from __future__ import annotations

from collections import deque

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import BoolArray, Float64Array, Int32Array, Int8Array


def apply_sea_level(
    *,
    elevation: Float64Array,
    target_land_fraction: float,
    n_cells: int,
) -> Float64Array:
    """Piecewise-normalise elevation to ``[-1, 1]`` with sea level at 0.

    Sea level is placed at the elevation percentile that leaves
    ``target_land_fraction`` of cells above it (e.g. 0.32 -> 32 %
    land).  Land cells are mapped to ``(0, 1]``, ocean cells to
    ``[-1, 0)``, and sea level is pinned at exactly 0.

    The input array is mutated in place --- no copy is made.

    Args:
        elevation: Per-cell raw elevation from the erosion loop
            (mutated in place).
        target_land_fraction: Desired fraction of cells above sea
            level (0.0--1.0).
        n_cells: Number of mesh cells (``geometry.n_cells``).

    Returns:
        ``is_land``: Boolean mask, True where elevation is at or
            above sea level.
    """
    # --- sea level by percentile ---
    sea_level: float = float(np.quantile(a=elevation, q=1.0 - target_land_fraction))

    is_land: BoolArray = elevation >= sea_level

    # --- piecewise normalise ---
    # Land:  (z - sea_level) / (land_max - sea_level)  ->  (0, 1]
    land_mask: BoolArray = is_land
    land_max: float = float(elevation[land_mask].max())
    land_range: float = land_max - sea_level
    if land_range > 0.0:
        elevation[land_mask] = (elevation[land_mask] - sea_level) / land_range

    # Ocean:  (z - ocean_min) / (sea_level - ocean_min) - 1  ->  [-1, 0)
    ocean_mask: BoolArray = ~is_land
    ocean_min: float = float(elevation[ocean_mask].min())
    ocean_range: float = sea_level - ocean_min
    if ocean_range > 0.0:
        elevation[ocean_mask] = (elevation[ocean_mask] - ocean_min) / ocean_range - 1.0

    return is_land


def label_landmasses(
    *,
    is_land: BoolArray,
    geometry: MeshGeometry,
    n_cells: int,
    island_min_fraction: float,
    landmass_min_fraction: float,
) -> tuple[Int32Array, Int8Array]:
    """Label connected land components via BFS and classify by component size.

    Every land cell is assigned a ``landmass_id`` (1-based component label;
    0 = ocean).  Components are then classified into four tiers by their
    size fraction of total cells:

    * 3 = major (>= ``landmass_min_fraction``)
    * 2 = landmass (>= ``island_min_fraction``)
    * 1 = island (below ``island_min_fraction``)
    * 0 = ocean (not land)

    Args:
        is_land: Boolean mask, True for land cells.
        geometry: Torus mesh with CSR adjacency.
        n_cells: Number of mesh cells.
        island_min_fraction: Minimum fraction of total cells for a
            component to be classed as a landmass (not island).
        landmass_min_fraction: Minimum fraction for a component to be
            classed as major.

    Returns:
        ``landmass_id``: 1-based connected component label per cell
            (0 = ocean).
        ``landmass_class``: Per-cell class (0 ocean, 1 island,
            2 landmass, 3 major).
    """
    landmass_id: Int32Array = np.zeros(shape=n_cells, dtype=np.int32)
    visited: BoolArray = np.zeros(shape=n_cells, dtype=bool)
    component_id: int = 0

    for cell_id in range(n_cells):
        if not is_land[cell_id] or visited[cell_id]:
            continue
        component_id += 1

        # BFS from this unvisited land cell.
        queue: deque[int] = deque()
        queue.append(cell_id)
        visited[cell_id] = True
        landmass_id[cell_id] = component_id

        while queue:
            current: int = queue.popleft()
            for neighbor_id in geometry.neighbors_of(cell_id=current):
                neighbor_id = int(neighbor_id)
                if not is_land[neighbor_id] or visited[neighbor_id]:
                    continue
                visited[neighbor_id] = True
                landmass_id[neighbor_id] = component_id
                queue.append(neighbor_id)

    # --- classify by size ---
    cell_counts: Float64Array = np.bincount(landmass_id).astype(np.float64)
    landmass_class: Int8Array = np.zeros(shape=n_cells, dtype=np.int8)

    for component in range(1, component_id + 1):
        size: int = int(cell_counts[component])
        size_fraction: float = size / n_cells
        if size_fraction >= landmass_min_fraction:
            landmass_class[landmass_id == component] = 3  # major
        elif size_fraction >= island_min_fraction:
            landmass_class[landmass_id == component] = 2  # landmass
        else:
            landmass_class[landmass_id == component] = 1  # island

    return landmass_id, landmass_class


def compute_coast_distance(
    *,
    is_land: BoolArray,
    geometry: MeshGeometry,
    n_cells: int,
) -> Float64Array:
    """Multi-source BFS from coastal land cells outward over land.

    Every coastal land cell seeds the BFS at distance 0; inland cells
    receive their hop count.  Ocean cells (``~is_land``) stay at 0.

    Args:
        is_land: Boolean mask, True for land cells.
        geometry: Torus mesh with CSR adjacency.
        n_cells: Number of mesh cells.

    Returns:
        ``coast_distance``: Per-cell hop distance from the nearest
            coast (0 for ocean and coastal cells).
    """
    coast_distance: Float64Array = np.zeros(shape=n_cells, dtype=np.float64)

    # --- identify coastal cells ---
    is_ocean: BoolArray = ~is_land
    coastal: BoolArray = np.zeros(shape=n_cells, dtype=bool)

    for cell_id in range(n_cells):
        if not is_land[cell_id]:
            continue
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if is_ocean[neighbor_id]:
                coastal[cell_id] = True
                break

    # --- multi-source BFS ---
    queue: deque[tuple[int, int]] = deque()
    visited: BoolArray = np.zeros(shape=n_cells, dtype=bool)

    for cell_id in range(n_cells):
        if coastal[cell_id]:
            coast_distance[cell_id] = 0.0
            visited[cell_id] = True
            queue.append((cell_id, 0))

    while queue:
        current, hops = queue.popleft()
        for neighbor_id in geometry.neighbors_of(cell_id=current):
            neighbor_id = int(neighbor_id)
            if visited[neighbor_id] or not is_land[neighbor_id]:
                continue
            visited[neighbor_id] = True
            dist: int = hops + 1
            coast_distance[neighbor_id] = float(dist)
            queue.append((neighbor_id, dist))

    return coast_distance


def compute_slope(
    *,
    elevation: Float64Array,
    geometry: MeshGeometry,
    n_cells: int,
) -> Float64Array:
    """Compute steepest-descent slope per cell.

    For each cell, slope is the maximum elevation drop to a neighbour
    divided by torus-aware distance.  Upward slopes (neighbour higher
    than the current cell) contribute nothing --- water flows downhill.

    Args:
        elevation: Per-cell normalised elevation in ``[-1, 1]``.
        geometry: Torus mesh with CSR adjacency.
        n_cells: Number of mesh cells.

    Returns:
        ``slope``: Per-cell maximum downward gradient.
    """
    slope: Float64Array = np.zeros(shape=n_cells, dtype=np.float64)
    width: float = geometry.width
    height: float = geometry.height
    sites: Float64Array = geometry.sites

    for cell_id in range(n_cells):
        z_i: float = float(elevation[cell_id])
        max_slope: float = 0.0
        site_i: Float64Array = sites[cell_id]

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            z_n: float = float(elevation[neighbor_id])
            if z_n >= z_i:
                continue

            drop: float = z_i - z_n
            dist: float = torus_distance(
                a=site_i,
                b=sites[neighbor_id],
                width=width,
                height=height,
            )
            if dist > 0.0:
                local_slope: float = drop / dist
                if local_slope > max_slope:
                    max_slope = local_slope

        slope[cell_id] = max_slope

    return slope
