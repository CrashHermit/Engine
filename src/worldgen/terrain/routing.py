from __future__ import annotations

import numpy as np
import heapq

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array, IntPArray


def priority_flood(
    *,
    geometry: MeshGeometry,
    z: Float64Array,
    base_cells: Int32Array,
) -> Float64Array:
    """Compute the water-surface elevation for flow routing.

    Barnes (2014) priority-flood: grow a water surface upward from
    base (ocean) cells through a min-heap ordered by water-surface
    elevation.  Every cell's ``z_route`` is the level water must reach
    to flow from that cell to the ocean — ``z`` for ridges, flat
    spill-level inside bowls.  The original terrain ``z`` is never
    mutated.

    A tiny ``eps * hops`` bias is baked into ``z_route`` itself so
    flat bowl floors drain toward the spill instead of dead-ending in
    a tie that ``compute_receivers`` cannot resolve.

    Args:
        geometry: Torus mesh with CSR adjacency.
        z: Per-cell ground elevation (float64).
        base_cells: Indices of cells treated as ocean / base level
            (typically the lowest ``base_level_fraction`` percentile
            of ``z``).

    Returns:
        z_route: Per-cell water-surface elevation (float64).
    """
    n: int = geometry.n_cells
    z_route: Float64Array = np.empty(n, dtype=np.float64)
    visited: BoolArray = np.zeros(n, dtype=bool)

    # Priority-flood uses the same min-heap pattern as plate growth
    # (plates.py), but keyed by water-surface elevation instead of
    # cumulative cost.
    eps: float = 1e-8
    heap: list[tuple[float, int, int]] = []

    # Seed the heap with base-level cells at their raw elevation.
    for cell_id in base_cells:
        z_val: float = float(z[cell_id])
        z_route[cell_id] = z_val
        visited[cell_id] = True
        heapq.heappush(heap, (float(z_route[cell_id]), 0, int(cell_id)))

    while heap:
        # Pop the lowest-water-surface unprocessed cell.
        current_z, hops, cell_id = heapq.heappop(heap)

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id: int = int(neighbor_id)
            if visited[neighbor_id]:
                continue

            # Water cannot descend below the level it arrived at.
            neighbor_z: float = float(z[neighbor_id])
            fill_z: float = max(current_z, neighbor_z)
            z_route[neighbor_id] = fill_z + eps * (hops + 1)
            visited[neighbor_id] = True

            heapq.heappush(
                heap,
                (float(z_route[neighbor_id]), hops + 1, int(neighbor_id)),
            )

    return z_route


def compute_receivers(
    *,
    geometry: MeshGeometry,
    z_route: Float64Array,
) -> Int32Array:
    """Build the downhill flow-direction tree.

    Each cell's receiver is its neighbour with the lowest
    ``z_route``, if that value is lower than the cell's own
    ``z_route``.  Cells with no downhill neighbour (pits,
    base level) stay at ``-1``.

    The ``eps * hops`` bias baked into ``z_route`` by
    ``priority_flood`` ensures flat bowl floors still have a
    downhill direction toward the spill, so this function
    needs no special tiebreaking logic.

    Args:
        geometry: Torus mesh with CSR adjacency.
        z_route: Per-cell water-surface elevation from
            ``priority_flood`` (float64).

    Returns:
        receiver: Per-cell downstream cell id (int32).
            ``-1`` marks pits and base-level cells.
    """
    n: int = geometry.n_cells
    # All cells start as pits (-1); only cells with a lower neighbour
    # get overwritten with a valid receiver.
    receiver: Int32Array = np.full(n, -1, dtype=np.int32)

    for cell_id in range(n):
        lowest_z: float = float("inf")
        lowest_neighbor: int = -1
        neighbors: Int32Array = geometry.neighbors_of(cell_id=cell_id)
        for neighbor_id in neighbors:
            neighbor_id: int = int(neighbor_id)
            if z_route[neighbor_id] < lowest_z:
                lowest_z = z_route[neighbor_id]
                lowest_neighbor = neighbor_id

        if lowest_z < z_route[cell_id]:
            receiver[cell_id] = lowest_neighbor

    return receiver


def accumulate_drainage(
    *,
    receiver: Int32Array,
    z_route: Float64Array,
) -> Float64Array:
    """Accumulate upstream cell count along the receiver flow tree.

    Every cell contributes 1 (its own "raindrop") and passes its
    accumulated total downstream to its receiver.  Processing from
    highest to lowest ``z_route`` guarantees every donor is complete
    before it hands off its total, so each cell is visited exactly
    once.

    Args:
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        z_route: Per-cell water-surface elevation from
            ``priority_flood`` (float64).  Used only for
            topological ordering.

    Returns:
        drainage: Per-cell upstream count (float64).  Raw values
            span 1 to thousands; use ``log(drainage)`` for
            visualisation.
    """
    n: int = len(receiver)
    drainage: Float64Array = np.ones(shape=n, dtype=np.float64)
    order: IntPArray = np.argsort(a=z_route)[::-1]

    for cell_id in order:
        r: int = int(receiver[cell_id])
        if r >= 0:
            drainage[r] += drainage[cell_id]

    return drainage
