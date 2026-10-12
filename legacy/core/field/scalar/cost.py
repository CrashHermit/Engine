"""Edge-weight builders for graph-based Voronoi tessellation.

Each builder consumes spatial or scalar data and produces a
``dict[tuple[int, int], float]`` mapping directed edges to their
traversal weight.  These dicts are passed to ``voronoi_msd``.

Builders iterate the adjacency list — positions and node values
are build-time inputs only; the resulting dict is pure graph data.
"""

import numpy as np


def euclidean(
    adjacency: list[list[int]],
    positions: np.ndarray,
) -> dict[tuple[int, int], float]:
    """Edge weights by Euclidean distance between vertex positions.

    Args:
        adjacency: Adjacency list, ``adjacency[i]`` lists neighbors of ``i``.
        positions: Vertex positions, shape ``(n, 3)``.

    Returns:
        Edge-weight dict for use with ``voronoi_msd``.
    """
    edge_weights: dict[tuple[int, int], float] = {}

    for source_node, neighbor_nodes in enumerate(adjacency):
        for target_node in neighbor_nodes:
            edge_weights[(source_node, target_node)] = float(
                np.linalg.norm(positions[source_node] - positions[target_node]),
            )

    return edge_weights

def noise_average(
    adjacency: list[list[int]],
    node_values: np.ndarray,
    strength: float
) -> dict[tuple[int, int], float]:
    edge_weights: dict[tuple[int, int], float] = {}

    for source_node, neighbor_nodes in enumerate(adjacency):
        for target_node in neighbor_nodes:
            average: float = (node_values[source_node] + node_values[target_node]) / 2.0
            edge_weights[(source_node, target_node)] = average * strength

    return edge_weights

def noise_multiplicative(
    adjacency: list[list[int]],
    node_values: np.ndarray,
    strength: float,
) -> dict[tuple[int, int], float]:
    """Edge weights from absolute noise difference, scaled by strength.

    Args:
        adjacency: Adjacency list, ``adjacency[i]`` lists neighbors of ``i``.
        node_values: Per-vertex noise values, shape ``(n,)``.
        strength: Multiplier applied to the noise gradient.

    Returns:
        Edge-weight dict for use with ``voronoi_msd``.
    """
    edge_weights: dict[tuple[int, int], float] = {}

    for source_node, neighbor_nodes in enumerate(adjacency):
        for target_node in neighbor_nodes:
            edge_weights[(source_node, target_node)] = (
                abs(node_values[source_node] - node_values[target_node]) * strength
            )

    return edge_weights
