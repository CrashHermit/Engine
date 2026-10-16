"""Procedural interaction strengths across plate boundaries."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import edge_frames


def boundary_interactions(
    mesh: Mesh,
    plate_ids: np.ndarray,
    plate_rotation: np.ndarray,
    boundary_edge_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return convergence, divergence and shear aligned with boundary edges.

    Evaluate both rotations at the normalized edge midpoint. Positive opening
    means divergence; negative opening means convergence. Shear is unsigned.
    Values retain the shared rotation scale rather than normalizing each field.
    """
    edges = mesh.edges[boundary_edge_indices]
    midpoint, across, along = edge_frames(mesh, boundary_edge_indices)
    left_rotation = plate_rotation[plate_ids[edges[:, 0]]]
    right_rotation = plate_rotation[plate_ids[edges[:, 1]]]
    relative_velocity = np.cross(right_rotation - left_rotation, midpoint)
    opening = np.sum(relative_velocity * across, axis=1)
    shear = np.abs(np.sum(relative_velocity * along, axis=1))
    return np.maximum(-opening, 0.0), np.maximum(opening, 0.0), shear
