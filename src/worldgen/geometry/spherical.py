"""Geometry helpers for unit-sphere meshes."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def angular_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Return great-circle angles between paired unit-sphere positions."""
    return np.arctan2(
        np.linalg.norm(np.cross(left, right), axis=1),
        np.sum(left * right, axis=1),
    )


def spherical_ring(
    positions: np.ndarray, angular_radius: float, sample_count: int = 8
) -> np.ndarray:
    """Return equally spaced geodesic samples around unit-sphere positions."""
    positions = np.asarray(positions, dtype=np.float64)
    reference_axes = np.eye(3, dtype=np.float64)[np.argmin(np.abs(positions), axis=1)]
    first_tangent = (
        reference_axes
        - np.sum(reference_axes * positions, axis=1, keepdims=True) * positions
    )
    first_tangent /= np.linalg.norm(first_tangent, axis=1, keepdims=True)
    second_tangent = np.cross(positions, first_tangent)

    bearings = 2.0 * np.pi * np.arange(sample_count, dtype=np.float64) / sample_count
    directions = (
        np.cos(bearings)[None, :, None] * first_tangent[:, None, :]
        + np.sin(bearings)[None, :, None] * second_tangent[:, None, :]
    )
    ring = (
        np.cos(angular_radius) * positions[:, None, :]
        + np.sin(angular_radius) * directions
    )
    ring /= np.linalg.norm(ring, axis=2, keepdims=True)
    return ring


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
