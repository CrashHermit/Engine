"""Mixed normal/shear transform boundary relief propagation."""

from collections.abc import Sequence

import numpy as np

from src.worldgen.elevation.config import TransformConfig
from src.worldgen.elevation.profiles import transform_profile
from src.worldgen.elevation.sources import boundary_side_sources
from src.worldgen.field.distance import nearest_source_distances
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geometry.mesh import Mesh


def transform_strength(normal: np.ndarray, shear: np.ndarray) -> np.ndarray:
    """Return signed normal/shear motion strength, with zero for a zero denominator."""
    denominator = np.abs(normal) + shear
    valid = denominator != 0.0
    strength = np.zeros_like(denominator, dtype=np.float64)
    strength[valid] = normal[valid] * shear[valid] / denominator[valid]
    return strength


def transform_relief(
    mesh: Mesh,
    config: TransformConfig,
    radius_m: float,
    *,
    lengths: np.ndarray,
    adjacency: Sequence[Sequence[tuple[int, float]]],
    crust: np.ndarray,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_normal: np.ndarray,
    boundary_shear: np.ndarray,
) -> np.ndarray | None:
    """Return signed relief induced by nearest mixed normal/shear boundary."""
    width = config.width_percent
    if width <= 0.0 or config.height_percent == 0.0:
        return None
    source_boundaries = [
        index
        for index in range(len(boundary_edge_indices))
        if boundary_normal[index] != 0.0
        and boundary_shear[index] != 0.0
        and abs(boundary_normal[index]) + boundary_shear[index] != 0.0
    ]
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
    relief = np.zeros(len(mesh.vertices), dtype=np.float64)
    peak_scale = radius_m * config.height_percent / 100.0
    source_strengths = transform_strength(boundary_normal, boundary_shear)
    for vertex in range(len(mesh.vertices)):
        source_id = int(winning_ids[vertex])
        if source_id < 0:
            continue
        boundary_index = source_id // 2
        relief[vertex] = (
            peak_scale
            * float(source_strengths[boundary_index])
            * transform_profile(distances[vertex], width)
        )
    return relief
