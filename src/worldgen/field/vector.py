"""Vector fields constrained to the spherical tangent plane."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def gradient(
    mesh: Mesh,
    node_values: np.ndarray,
    *,
    descending: bool = False,
) -> np.ndarray:
    """Estimate a tangent-plane scalar gradient from neighboring cells."""
    source = mesh.edges[:, 0]
    target = mesh.edges[:, 1]
    deltas = mesh.vertices[target] - mesh.vertices[source]
    differences = node_values[target] - node_values[source]
    if descending:
        differences = -differences
    weighted = deltas * differences[:, np.newaxis]
    result = np.zeros_like(mesh.vertices)
    np.add.at(result, source, weighted)
    np.add.at(result, target, weighted)
    radial = np.sum(result * mesh.vertices, axis=1, keepdims=True)
    return result - radial * mesh.vertices


def rotate_tangent(positions: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """Rotate tangent vectors by ninety degrees around the sphere normal."""
    return np.cross(positions, vectors)
