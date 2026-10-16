"""Geometry helpers for unit-sphere meshes."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def angular_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Return great-circle angles between paired unit-sphere positions."""
    return np.arctan2(
        np.linalg.norm(np.cross(left, right), axis=1),
        np.sum(left * right, axis=1),
    )


def edge_lengths_percent(mesh: Mesh) -> np.ndarray:
    """Return mesh edge lengths as percentages of circumference."""
    left = mesh.vertices[mesh.edges[:, 0]]
    right = mesh.vertices[mesh.edges[:, 1]]
    return angular_distances(left, right) * (100.0 / (2.0 * np.pi))


def edge_frames(
    mesh: Mesh, edge_indices: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return midpoint, across, and along vectors for selected edges."""
    edges = mesh.edges[edge_indices]
    left = mesh.vertices[edges[:, 0]]
    right = mesh.vertices[edges[:, 1]]
    midpoint = left + right
    midpoint /= np.linalg.norm(midpoint, axis=1, keepdims=True)
    across = right - left
    across /= np.linalg.norm(across, axis=1, keepdims=True)
    along = np.cross(midpoint, across)
    return midpoint, across, along
