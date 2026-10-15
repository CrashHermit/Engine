"""Graph-distance coastal base elevation generation."""

import heapq

import numpy as np

from src.worldgen.field.partition import region_boundary_edges
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.terrain.config import TerrainConfig
from src.worldgen.terrain.model import TerrainResult


def _edge_lengths_percent(mesh: Mesh) -> np.ndarray:
    """Measure great-circle edge lengths as percentages of circumference."""
    left = mesh.vertices[mesh.edges[:, 0]]
    right = mesh.vertices[mesh.edges[:, 1]]
    angles = np.arctan2(
        np.linalg.norm(np.cross(left, right), axis=1),
        np.sum(left * right, axis=1),
    )
    return angles * (100.0 / (2.0 * np.pi))


def _signed_margin_distances(
    mesh: Mesh,
    continental_mask: np.ndarray,
    coast_edge_indices: np.ndarray,
    edge_lengths_percent: np.ndarray,
) -> np.ndarray:
    """Propagate margin distances through each crust class on the mesh graph."""
    distances = np.full(len(mesh.vertices), np.inf, dtype=np.float64)
    edge_lookup = {
        (int(left), int(right)): index for index, (left, right) in enumerate(mesh.edges)
    }
    queue: list[tuple[float, int]] = []
    for edge_index_value in coast_edge_indices:
        edge_index = int(edge_index_value)
        left, right = mesh.edges[edge_index]
        initial = edge_lengths_percent[edge_index] * 0.5
        for vertex_value in (left, right):
            vertex = int(vertex_value)
            if initial < distances[vertex]:
                distances[vertex] = initial
                heapq.heappush(queue, (initial, vertex))

    while queue:
        distance, vertex = heapq.heappop(queue)
        if distance != distances[vertex]:
            continue
        start = mesh.neighbor_offsets[vertex]
        end = mesh.neighbor_offsets[vertex + 1]
        for neighbor_value in mesh.neighbor_indices[start:end]:
            neighbor = int(neighbor_value)
            if continental_mask[neighbor] != continental_mask[vertex]:
                continue
            edge_index = edge_lookup[(min(vertex, neighbor), max(vertex, neighbor))]
            candidate = distance + edge_lengths_percent[edge_index]
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))

    return np.where(continental_mask, distances, -distances)


def _smoothstep(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def _base_elevation(
    margin_distance: np.ndarray, config: TerrainConfig, radius_m: float
) -> np.ndarray:
    """Apply the saturated smooth coastal profile to signed margin distance."""
    distance = config.shelf_width_percent - margin_distance
    inland = _smoothstep(
        (distance + config.inland_width_percent) / config.inland_width_percent
    )
    shelf = _smoothstep(distance / config.shelf_width_percent)
    slope = _smoothstep(
        (distance - config.shelf_width_percent) / config.slope_width_percent
    )
    return (
        config.interior_height_percent * (1.0 - inland)
        - config.shelf_depth_percent * shelf
        - (config.basin_depth_percent - config.shelf_depth_percent) * slope
    ) * (radius_m / 100.0)


def generate_terrain(
    mesh: Mesh, continental_mask: np.ndarray, config: TerrainConfig, radius_m: float
) -> TerrainResult:
    """Generate signed graph distances and coarse base elevations."""
    coast_edge_indices = region_boundary_edges(mesh, continental_mask)
    lengths = _edge_lengths_percent(mesh)
    margin_distance = _signed_margin_distances(
        mesh, continental_mask, coast_edge_indices, lengths
    )
    base_elevation = _base_elevation(margin_distance, config, radius_m)
    land_mask = base_elevation >= 0.0
    for array in (margin_distance, base_elevation, land_mask):
        array.setflags(write=False)
    return TerrainResult(
        margin_distance=margin_distance,
        base_elevation=base_elevation,
        land_mask=land_mask,
        coast_edge_indices=coast_edge_indices,
        elevation_range_m=(
            -config.basin_depth_percent * radius_m / 100.0,
            config.interior_height_percent * radius_m / 100.0,
        ),
    )
