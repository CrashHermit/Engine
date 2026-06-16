from __future__ import annotations

import numpy as np
import heapq

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def priority_flood(
    *,
    geometry: MeshGeometry,
    z: Float64Array,
    base_cells: Int32Array,
    config: ErosionConfig,
) -> Float64Array:
    """Compute z_route: water-surface elevation after filling bowls."""
    n: int = geometry.n_cells
    z_route: Float64Array = np.empty(n, dtype=np.float64)
    visited: BoolArray = np.zeros(n, dtype=bool)

    eps: float = 1e-8

    heap: list[tuple[float, int, int]] = []

    for cell_id in base_cells:
        z_val: float = float(z[cell_id])
        z_route[cell_id] = z_val
        visited[cell_id] = True
        heapq.heappush(heap, (z_route[cell_id], 0, cell_id))

    while heap:
        current_z, hops, cell_id = heapq.heappop(heap)

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if visited[neighbor_id]:
                continue

            neighbor_z: float = float(z[neighbor_id])
            fill_z: float = max(z_route[cell_id], neighbor_z)
            z_route[neighbor_id] = fill_z + eps * (hops + 1)
            visited[neighbor_id] = True

            heapq.heappush(
                heap,
                (z_route[neighbor_id], hops + 1, neighbor_id),
            )

    return z_route


def compute_receivers(
    *,
    geometry: MeshGeometry,
    z_route: Float64Array,
) -> Int32Array:
    """Return receiver array: downstream cell id for each cell, -1 = base level."""
    n: int = geometry.n_cells
    receiver: Int32Array = np.full(n, -1, dtype=np.int32)

    for cell_id in range(n):
        lowest_z = float('inf')
        lowest_neighbor: int = -1
        neighbors: Int32Array = geometry.neighbors_of(cell_id=cell_id)
        for neighbor_id in neighbors:
            if z_route[neighbor_id] < lowest_z:
                lowest_z = z_route[neighbor_id]
                lowest_neighbor = neighbor_id

        if lowest_z < z_route[cell_id]:
            receiver[cell_id] = lowest_neighbor
        else:
            receiver[cell_id] = -1

    return receiver
