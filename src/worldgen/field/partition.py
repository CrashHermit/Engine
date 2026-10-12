"""Weighted graph region assignment."""

import heapq

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def weighted_regions(
    mesh: Mesh,
    seed_indices: np.ndarray,
    edge_costs: np.ndarray,
) -> np.ndarray:
    """Assign each cell to its cheapest seed using multi-source Dijkstra."""
    edge_lookup = {
        (int(left), int(right)): index for index, (left, right) in enumerate(mesh.edges)
    }
    seed_owners = {
        int(cell_id): plate_id for plate_id, cell_id in enumerate(seed_indices)
    }
    distances = np.full(len(mesh.vertices), np.inf, dtype=np.float64)
    owners = np.full(len(mesh.vertices), -1, dtype=np.int64)
    queue: list[tuple[float, int, int]] = []
    for plate_id, cell_id in enumerate(seed_indices):
        cell = int(cell_id)
        distances[cell] = 0.0
        owners[cell] = plate_id
        heapq.heappush(queue, (0.0, plate_id, cell))

    while queue:
        distance, plate_id, cell = heapq.heappop(queue)
        if distance != distances[cell] or plate_id != owners[cell]:
            continue
        start = mesh.neighbor_offsets[cell]
        end = mesh.neighbor_offsets[cell + 1]
        for neighbor_value in mesh.neighbor_indices[start:end]:
            neighbor = int(neighbor_value)
            if neighbor in seed_owners:
                continue
            edge = (min(cell, neighbor), max(cell, neighbor))
            candidate_distance = distance + edge_costs[edge_lookup[edge]]
            candidate_owner = plate_id
            if candidate_distance < distances[neighbor] or (
                candidate_distance == distances[neighbor]
                and candidate_owner < owners[neighbor]
            ):
                distances[neighbor] = candidate_distance
                owners[neighbor] = candidate_owner
                heapq.heappush(queue, (candidate_distance, candidate_owner, neighbor))
    return owners
