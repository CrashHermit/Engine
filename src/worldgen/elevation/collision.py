"""Continental collision mountain-belt relief propagation."""

import heapq
from collections.abc import Sequence

import numpy as np

from src.worldgen.elevation.config import CollisionConfig
from src.worldgen.elevation.profiles import collision_profile
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh


def collision_relief(
    mesh: Mesh,
    config: CollisionConfig,
    radius_m: float,
    *,
    lengths: np.ndarray,
    adjacency: Sequence[Sequence[tuple[int, float]]],
    crust: np.ndarray,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_convergence: np.ndarray,
    positive: np.ndarray,
) -> None:
    """Max-combine collision source profiles into shared relief envelopes."""
    width = config.width_percent
    if width <= 0.0 or config.height_percent == 0.0:
        return
    peak_scale = radius_m * config.height_percent / 100.0

    def propagate(edge_index: int, side: int, motion: float) -> None:
        if motion <= 0.0:
            return
        edge = int(boundary_edge_indices[edge_index])
        endpoints = mesh.edges[edge]
        section = int(boundary_sections.edge_section_ids[edge_index])
        plate = int(boundary_sections.plate_pairs[section, side])
        source_vertices = [
            int(vertex)
            for vertex in endpoints
            if plate_ids[vertex] == plate
            and crust[vertex] == boundary_sections.continental_sides[section, side]
        ]
        if not source_vertices:
            return
        initial = float(lengths[edge]) * 0.5
        distances = np.full(len(mesh.vertices), np.inf, dtype=np.float64)
        queue: list[tuple[float, int]] = []
        for vertex in source_vertices:
            distances[vertex] = initial
            heapq.heappush(queue, (initial, vertex))
        peak = peak_scale * float(motion)
        while queue:
            distance, vertex = heapq.heappop(queue)
            if distance != distances[vertex] or distance >= width:
                continue
            broad, crest_weight = collision_profile(
                distance, width, config.crest_width_fraction
            )
            contribution = peak * broad
            contribution += peak * config.crest_height_multiplier * crest_weight
            if contribution > positive[vertex]:
                positive[vertex] = contribution
            for neighbor, edge_length in adjacency[vertex]:
                if plate_ids[neighbor] != plate or crust[neighbor] != crust[vertex]:
                    continue
                candidate = distance + edge_length
                if candidate < width and candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    heapq.heappush(queue, (candidate, neighbor))

    for boundary_index in range(len(boundary_edge_indices)):
        section = int(boundary_sections.edge_section_ids[boundary_index])
        motion = float(boundary_convergence[boundary_index])
        if motion > 0.0 and boundary_sections.continental_sides[section].all():
            for side in range(2):
                propagate(boundary_index, side, motion)
