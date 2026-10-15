"""Discrete region assignment by Dijkstra or connected competitive flooding."""

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


def priority_flood_regions(
    mesh: Mesh,
    seed_indices: np.ndarray,
    priorities: np.ndarray,
) -> np.ndarray:
    """Claim cells through the lowest frontier barrier, preserving connectivity.

    Priorities have shape (region count, cell count). A claim is final; this is
    competitive growth, not independent shortest paths or global minimax labels.
    Equal barriers prefer the lower region ID, then the lower cell ID.
    """
    owners = np.full(len(mesh.vertices), -1, dtype=np.int64)
    owners[seed_indices] = np.arange(len(seed_indices))
    queue: list[tuple[float, int, int]] = []

    def expand(cell: int, region: int, barrier: float) -> None:
        start = mesh.neighbor_offsets[cell]
        end = mesh.neighbor_offsets[cell + 1]
        for neighbor_value in mesh.neighbor_indices[start:end]:
            neighbor = int(neighbor_value)
            if owners[neighbor] == -1:
                candidate = max(barrier, priorities[region, neighbor])
                heapq.heappush(queue, (candidate, region, neighbor))

    for region, cell in enumerate(seed_indices):
        expand(int(cell), region, -np.inf)
    while queue:
        barrier, region, cell = heapq.heappop(queue)
        if owners[cell] != -1:
            continue
        owners[cell] = region
        expand(cell, region, barrier)
    return owners


def region_boundary_edges(mesh: Mesh, region_ids: np.ndarray) -> np.ndarray:
    """Return read-only edge indices connecting cells with different labels."""
    indices = np.flatnonzero(
        region_ids[mesh.edges[:, 0]] != region_ids[mesh.edges[:, 1]]
    ).astype(np.int64)
    indices.setflags(write=False)
    return indices
