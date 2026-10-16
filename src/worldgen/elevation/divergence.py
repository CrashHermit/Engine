"""Divergent ridge and rift relief propagation."""

from collections.abc import Sequence

import numpy as np

from src.worldgen.elevation.config import DivergenceConfig
from src.worldgen.elevation.profiles import divergent_profile
from src.worldgen.field.distance import nearest_source_distances
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.elevation.sources import boundary_side_sources


def divergence_relief(
    mesh: Mesh,
    config: DivergenceConfig,
    radius_m: float,
    *,
    lengths: np.ndarray,
    adjacency: Sequence[Sequence[tuple[int, float]]],
    crust: np.ndarray,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_divergence: np.ndarray,
) -> np.ndarray | None:
    """Evaluate the nearest divergent boundary-side source per vertex."""
    width = config.width_percent
    if width <= 0.0 or config.height_percent == 0.0:
        return None
    vertex_count = len(mesh.vertices)
    source_boundaries = []
    for index in range(len(boundary_edge_indices)):
        if boundary_divergence[index] <= 0.0:
            continue
        source_boundaries.append(index)
    source_indices, source_distances, source_ids, region_ids = boundary_side_sources(
        mesh,
        lengths,
        plate_ids,
        crust,
        boundary_edge_indices,
        boundary_sections,
        source_boundaries,
    )
    distances, winning_ids = nearest_source_distances(
        adjacency,
        source_indices,
        source_distances,
        source_ids,
        region_ids,
        max_distance=width,
    )
    relief = np.zeros(vertex_count, dtype=np.float64)
    peak_scale = radius_m * config.height_percent / 100.0
    for vertex in range(vertex_count):
        source_id = int(winning_ids[vertex])
        if source_id < 0:
            continue
        boundary_index, _ = divmod(source_id, 2)
        relief[vertex] = (
            peak_scale
            * float(boundary_divergence[boundary_index])
            * divergent_profile(
                distances[vertex],
                width,
                bool(crust[vertex]),
                axial_width_fraction=config.axial_width_fraction,
                axial_depth_multiplier=config.axial_depth_multiplier,
                shoulder_height_multiplier=config.shoulder_height_multiplier,
            )
        )
    return relief
