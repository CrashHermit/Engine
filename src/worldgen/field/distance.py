"""Graph distance propagation helpers."""

import heapq
from collections.abc import Sequence

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def weighted_adjacency(
    mesh: Mesh, edge_lengths: np.ndarray
) -> list[list[tuple[int, float]]]:
    """Return sorted mesh neighbors paired with their edge lengths."""
    adjacency: list[list[tuple[int, float]]] = [[] for _ in range(len(mesh.vertices))]
    for vertex, neighbors in enumerate(adjacency):
        start = int(mesh.neighbor_offsets[vertex])
        end = int(mesh.neighbor_offsets[vertex + 1])
        for neighbor_value, edge_index in zip(
            mesh.neighbor_indices[start:end],
            mesh.neighbor_edge_indices[start:end],
        ):
            neighbor = int(neighbor_value)
            neighbors.append((neighbor, float(edge_lengths[edge_index])))
    return adjacency


def nearest_source_distances(
    adjacency: Sequence[Sequence[tuple[int, float]]],
    source_indices: np.ndarray,
    source_distances: np.ndarray,
    source_ids: np.ndarray,
    region_ids: np.ndarray,
    *,
    max_distance: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Propagate nearest source distances and IDs without crossing regions."""
    vertex_count = len(adjacency)
    distances = np.full(vertex_count, np.inf, dtype=np.float64)
    winning_source_ids = np.full(vertex_count, -1, dtype=np.int64)
    queue: list[tuple[float, int, int]] = []
    for source_value, distance_value, source_id_value in zip(
        source_indices, source_distances, source_ids
    ):
        source = int(source_value)
        distance = float(distance_value)
        source_id = int(source_id_value)
        if distance < distances[source] or (
            distance == distances[source] and source_id < winning_source_ids[source]
        ):
            distances[source] = distance
            winning_source_ids[source] = source_id
            heapq.heappush(queue, (distance, source_id, source))

    while queue:
        distance, source_id, vertex = heapq.heappop(queue)
        if (
            distance != distances[vertex]
            or source_id != winning_source_ids[vertex]
            or distance > max_distance
        ):
            continue
        for neighbor, edge_length in adjacency[vertex]:
            if region_ids[neighbor] != region_ids[vertex]:
                continue
            candidate = distance + edge_length
            if candidate > max_distance:
                continue
            if candidate < distances[neighbor] or (
                candidate == distances[neighbor]
                and source_id < winning_source_ids[neighbor]
            ):
                distances[neighbor] = candidate
                winning_source_ids[neighbor] = source_id
                heapq.heappush(queue, (candidate, source_id, neighbor))
    return distances, winning_source_ids


def multi_source_distances(
    mesh: Mesh,
    source_indices: np.ndarray,
    source_distances: np.ndarray,
    edge_lengths: np.ndarray,
    region_ids: np.ndarray,
    *,
    adjacency: Sequence[Sequence[tuple[int, float]]] | None = None,
) -> np.ndarray:
    """Propagate shortest distances without crossing region labels."""
    distances, _ = nearest_source_distances(
        adjacency if adjacency is not None else weighted_adjacency(mesh, edge_lengths),
        source_indices,
        source_distances,
        source_indices,
        region_ids,
        max_distance=np.inf,
    )
    return distances
