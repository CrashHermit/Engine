"""Graph edge costs derived from geometry and scalar fields."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def field_traversal_cost(
    mesh: Mesh, node_values: np.ndarray, irregularity_strength: float = 1.0
) -> np.ndarray:
    """Weight spherical edge distance by the average endpoint field value."""
    left = mesh.vertices[mesh.edges[:, 0]]
    right = mesh.vertices[mesh.edges[:, 1]]
    distance = np.arctan2(
        np.linalg.norm(np.cross(left, right), axis=1),
        np.sum(left * right, axis=1),
    )
    multipliers = 1.0 + irregularity_strength * node_values
    average_multiplier = (
        multipliers[mesh.edges[:, 0]] + multipliers[mesh.edges[:, 1]]
    ) / 2.0
    return distance * average_multiplier
