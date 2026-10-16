"""Coastal elevation calculations shared by the elevation generator."""

import numpy as np

from src.worldgen.field.distance import multi_source_distances
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.elevation.config import CoastalWidthConfig, ElevationConfig
from src.worldgen.utilities.curves import smoothstep


def _signed_margin_distances(
    mesh: Mesh,
    continental_mask: np.ndarray,
    crust_boundary_edge_indices: np.ndarray,
    edge_lengths_percent: np.ndarray,
) -> np.ndarray:
    """Propagate margin distances through each crust class on the mesh graph."""
    edges = mesh.edges[crust_boundary_edge_indices]
    source_indices = edges.reshape(-1)
    source_distances = np.repeat(
        edge_lengths_percent[crust_boundary_edge_indices] * 0.5, 2
    )
    distances = multi_source_distances(
        mesh,
        source_indices,
        source_distances,
        edge_lengths_percent,
        continental_mask,
    )
    return np.where(continental_mask, distances, -distances)


def _sample_width(
    positions: np.ndarray, config: CoastalWidthConfig, *, noise_seed: int
) -> np.ndarray:
    """Sample broad, continuous width variation without sample-set normalization."""
    return config.base_percent * noise_multiplier(
        positions,
        seed=noise_seed,
        frequency=config.noise_frequency,
        strength=config.variation_strength,
    )


def _base_elevation(
    margin_distance: np.ndarray,
    config: ElevationConfig,
    radius_m: float,
    *,
    density_anomaly: np.ndarray,
    inland_width: np.ndarray,
    shelf_width: np.ndarray,
    slope_width: np.ndarray,
) -> np.ndarray:
    """Apply the saturated smooth coastal profile to signed margin distance."""
    distance = shelf_width - margin_distance
    inland = smoothstep((distance + inland_width) / inland_width)
    shelf = smoothstep(distance / shelf_width)
    slope = smoothstep((distance - shelf_width) / slope_width)
    interior_target = (
        config.interior_height_percent
        - config.buoyancy.continental_height_percent * density_anomaly
    )
    basin_target = (
        config.basin_depth_percent
        + config.buoyancy.oceanic_height_percent * density_anomaly
    )
    return (
        interior_target * (1.0 - inland)
        - config.shelf_depth_percent * shelf
        - (basin_target - config.shelf_depth_percent) * slope
    ) * (radius_m / 100.0)
