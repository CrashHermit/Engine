from __future__ import annotations

import heapq
import random

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Int32Array

UNCLAIMED: int = -1


def build_plates(
    geometry: MeshGeometry,
    n_plates: int,
    seed: int,
    growth_raggedness: float,
) -> Int32Array:
    """Partition the mesh into contiguous plates via priority-queue growth.

    Returns one plate id per cell in ``[0, n_plates)``. Growth uses a min-heap
    keyed by cumulative cost plus random raggedness so borders are organic.
    """
    if n_plates < 1:
        msg: str = "n_plates must be at least 1"
        raise ValueError(msg)
    if n_plates > geometry.n_cells:
        msg: str = f"n_plates ({n_plates}) cannot exceed cell count ({geometry.n_cells})"
        raise ValueError(msg)

    rng: random.Random = random.Random(seed)
    n_cells: int = geometry.n_cells
    plate_id: Int32Array = np.full(n_cells, UNCLAIMED, dtype=np.int32)

    seed_cells: list[int] = rng.sample(population=range(n_cells), k=n_plates)

    heap: list[tuple[float, int, int]] = []
    plate: int
    cell: int
    for plate, cell in enumerate(seed_cells):
        heapq.heappush(heap, (0.0, cell, plate))

    while heap:
        cost, cell, plate = heapq.heappop(heap)
        if plate_id[cell] != UNCLAIMED:
            continue
        plate_id[cell] = plate

        for neighbor_id in geometry.neighbors_of(cell_id=cell):
            neighbor_id: int = int(neighbor_id)
            if plate_id[neighbor_id] == UNCLAIMED:
                priority: float = cost + 1.0 + rng.random() * growth_raggedness
                heapq.heappush(heap, (priority, neighbor_id, plate))

    return plate_id