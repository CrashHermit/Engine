"""Graph edge costs derived from geometry and scalar fields."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import angular_distances


def field_traversal_cost(
    mesh: Mesh, node_values: np.ndarray, irregularity_strength: float = 1.0
) -> np.ndarray:
    """Weight spherical edge distance by the average endpoint field value."""
    left = mesh.vertices[mesh.edges[:, 0]]
    right = mesh.vertices[mesh.edges[:, 1]]
    distance = angular_distances(left, right)
    multipliers = 1.0 + irregularity_strength * node_values
    average_multiplier = (
        multipliers[mesh.edges[:, 0]] + multipliers[mesh.edges[:, 1]]
    ) / 2.0
    return distance * average_multiplier
