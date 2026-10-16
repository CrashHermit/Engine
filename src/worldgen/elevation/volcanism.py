"""Compact hotspot shield relief on assigned plates."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import angular_distances
from src.worldgen.geology.model import HotspotResult
from src.worldgen.elevation.profiles import shield_profile


def volcanic_relief(
    mesh: Mesh,
    plate_ids: np.ndarray,
    hotspots: HotspotResult,
    radius_m: float,
) -> np.ndarray:
    """Build non-stacking compact shield uplift centered on generated hotspots."""
    relief = np.zeros(len(mesh.vertices), dtype=np.float64)
    for seed_index, plate_id, width_percent, height_percent in zip(
        hotspots.seed_indices,
        hotspots.plate_ids,
        hotspots.widths_percent,
        hotspots.heights_percent,
    ):
        width = float(width_percent)
        if width <= 0.0 or height_percent <= 0.0:
            continue
        center = mesh.vertices[int(seed_index)]
        distances = angular_distances(
            mesh.vertices, np.broadcast_to(center, mesh.vertices.shape)
        ) * (100.0 / (2.0 * np.pi))
        response = np.zeros(len(mesh.vertices), dtype=np.float64)
        support = (plate_ids == plate_id) & (distances < width)
        response[support] = shield_profile(distances[support], width)
        response *= radius_m * float(height_percent) / 100.0
        np.maximum(relief, response, out=relief)
    return relief
