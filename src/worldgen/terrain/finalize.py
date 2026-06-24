from collections import deque

import numpy as np

from src.worldgen.geometry.field_ops import diffuse
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import BoolArray, Float64Array, Int32Array, Int8Array


def smooth_elevation(
    *,
    elevation: Float64Array,
    geometry: MeshGeometry,
    passes: int,
    strength: float,
) -> Float64Array:
    """Lightly relax elevation toward the neighbor mean to de-speckle coastlines.

    The raw eroded terrain carries high-frequency wiggle that, once cut at sea
    level, surfaces as one-cell peninsulas, inlets, and islets — the "fuzzy"
    Voronoi-scale coastline.  A couple of gentle Laplacian passes
    (``z += strength * (mean_neighbor_z - z)``) damp that wiggle while leaving
    large-scale relief intact.  Run *before* the sea-level cut so the percentile
    placement (and therefore land fraction) is computed on the smoothed field.

    Args:
        elevation: Per-cell raw elevation from erosion.
        geometry: Torus mesh with CSR adjacency.
        passes: Number of relaxation passes (``<= 0`` returns the input as-is).
        strength: Blend toward the neighbor mean per pass, in ``[0, 1]``.

    Returns:
        The smoothed elevation (a new array; the input is not mutated).
    """
    return diffuse(
        geometry=geometry, field=elevation, strength=strength, passes=passes
    )


def _normalize_at_sea_level(
    *, elevation: Float64Array, sea_level: float
) -> BoolArray:
    """Piecewise-normalise elevation to ``[-1, 1]`` about a given sea level.

    Land cells map to ``(0, 1]``, ocean cells to ``[-1, 0)``, sea level pinned
    at exactly 0.  The input array is mutated in place.

    Args:
        elevation: Per-cell raw elevation (mutated in place).
        sea_level: The elevation value treated as sea level.

    Returns:
        ``is_land``: Boolean mask, True where elevation is at or above sea level.
    """
    is_land: BoolArray = elevation >= sea_level

    # Land:  (z - sea_level) / (land_max - sea_level)  ->  (0, 1]
    land_mask: BoolArray = is_land
    if np.any(land_mask):
        land_max: float = float(elevation[land_mask].max())
        land_range: float = land_max - sea_level
        if land_range > 0.0:
            elevation[land_mask] = (elevation[land_mask] - sea_level) / land_range

    # Ocean:  (z - ocean_min) / (sea_level - ocean_min) - 1  ->  [-1, 0)
    ocean_mask: BoolArray = ~is_land
    if np.any(ocean_mask):
        ocean_min: float = float(elevation[ocean_mask].min())
        ocean_range: float = sea_level - ocean_min
        if ocean_range > 0.0:
            elevation[ocean_mask] = (
                elevation[ocean_mask] - ocean_min
            ) / ocean_range - 1.0

    return is_land


def apply_sea_level(
    *,
    elevation: Float64Array,
    target_land_fraction: float,
) -> BoolArray:
    """Piecewise-normalise elevation with sea level at a land-fraction quota.

    Sea level is placed at the elevation percentile that leaves
    ``target_land_fraction`` of cells above it.  Retained as a utility (e.g.
    the clamp bounds in :func:`apply_sea_level_datum` and direct tests); the
    pipeline uses the emergent :func:`apply_sea_level_datum`.

    The input array is mutated in place.

    Args:
        elevation: Per-cell raw elevation (mutated in place).
        target_land_fraction: Desired fraction of cells above sea level.

    Returns:
        ``is_land``: Boolean mask, True where elevation is at or above sea level.
    """
    sea_level: float = float(np.quantile(a=elevation, q=1.0 - target_land_fraction))
    return _normalize_at_sea_level(elevation=elevation, sea_level=sea_level)


def _otsu_sea_level(elevation: Float64Array, bins: int = 256) -> float:
    """Otsu threshold over the elevation histogram: the ocean/continent split.

    Eroded terrain is bimodal — a low oceanic mode and a high continental
    (freeboard) mode.  Otsu's method finds the threshold between the two modes
    that maximizes between-class variance, i.e. the natural sea-level datum in
    the valley of the hypsometry.  Parameter-free and deterministic, so land
    fraction *emerges* from how much crust rides high rather than being forced
    to a quota.

    Args:
        elevation: Per-cell raw elevation.
        bins: Histogram resolution.

    Returns:
        The elevation value of the Otsu threshold (sea-level datum).
    """
    hist, edges = np.histogram(elevation, bins=bins)
    centers: Float64Array = 0.5 * (edges[:-1] + edges[1:])
    weight: Float64Array = hist.astype(np.float64)
    total: float = float(weight.sum())
    if total <= 0.0:
        return float(np.median(elevation))
    weight /= total

    cum_w: Float64Array = np.cumsum(weight)
    cum_mean: Float64Array = np.cumsum(weight * centers)
    global_mean: float = float(cum_mean[-1])

    denom: Float64Array = cum_w * (1.0 - cum_w)
    between: Float64Array = np.where(
        denom > 0.0,
        (global_mean * cum_w - cum_mean) ** 2 / np.where(denom > 0.0, denom, 1.0),
        0.0,
    )
    return float(centers[int(np.argmax(between))])


def apply_sea_level_datum(
    *,
    elevation: Float64Array,
    datum_bias: float,
    land_fraction_clamp: tuple[float, float],
) -> BoolArray:
    """Emergent sea level from a hypsometric datum, with a removable clamp.

    Places sea level at the Otsu ocean/continent split (so land fraction
    emerges per seed), shifts it by ``datum_bias`` standard deviations
    (+ raises sea level -> less land), then clamps the realized land fraction
    into ``land_fraction_clamp`` so a seed can't go all-ocean or all-land.
    Widen the clamp to ``(0.0, 1.0)`` to disable the guardrails entirely.

    The input array is mutated in place (piecewise-normalised).

    Args:
        elevation: Per-cell raw elevation (mutated in place).
        datum_bias: Sea-level shift in elevation standard deviations.
        land_fraction_clamp: ``(lo, hi)`` bounds on the realized land fraction.

    Returns:
        ``is_land``: Boolean mask, True where elevation is at or above sea level.
    """
    sea_level: float = _otsu_sea_level(elevation)
    sea_level += datum_bias * float(np.std(elevation))

    lo, hi = land_fraction_clamp
    fraction: float = float(np.mean(elevation >= sea_level))
    if fraction < lo:
        sea_level = float(np.quantile(a=elevation, q=1.0 - lo))
    elif fraction > hi:
        sea_level = float(np.quantile(a=elevation, q=1.0 - hi))

    return _normalize_at_sea_level(elevation=elevation, sea_level=sea_level)


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
