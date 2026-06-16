from __future__ import annotations

import numpy as np
import heapq

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Float64Array, Int32Array


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
    visited: np.ndarray = np.zeros(n, dtype=bool)

    eps: float = 1e-8

    heap: list[tuple[float, int, int]] = []

    for cell_id in base_cells:
        z_val: float = float(z[cell_id])
        z_route[cell_id] = z_val
        visited[cell_id] = True
        heapq.heappush(heap, (z_val + eps * 0, 0, cell_id))

    while heap:
        current_z, hops, cell_id = heapq.heappop(heap)

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if visited[neighbor_id]:
                continue

            neighbor_z: float = float(z[neighbor_id])
            fill_z: float = max(current_z, neighbor_z)
            z_route[neighbor_id] = fill_z
            visited[neighbor_id] = True

            heapq.heappush(
                heap,
                (fill_z + eps * (hops + 1), hops + 1, neighbor_id),
            )

    return z_route


def compute_receivers(
    geometry: MeshGeometry,
    z_route: Float64Array,
) -> Int32Array:
    """Return receiver array: downstream cell id for each cell, -1 = base level."""
    for cell_id in z_route:
        neighbors = geometry.neighbors_of(cell_id=cell_id)
