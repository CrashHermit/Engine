"""Graph edge costs derived from scalar fields."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def noise_difference_cost(mesh: Mesh, node_values: np.ndarray) -> np.ndarray:
    """Return absolute scalar differences for mesh undirected edges."""
    return np.abs(node_values[mesh.edges[:, 0]] - node_values[mesh.edges[:, 1]])
