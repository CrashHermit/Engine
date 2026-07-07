"""Gradient of a scalar field over a mesh on the unit sphere."""

import numpy as np


def gradient(
    positions: np.ndarray,
    adjacency: list[list[int]],
    node_values: np.ndarray,
    descending: bool = False,
) -> np.ndarray:
    """Per-vertex gradient of a scalar field on a unit-sphere mesh.

    Computes the tangent-plane gradient by accumulating weighted edge
    vectors and projecting the radial component out.

    Args:
        positions: Vertex positions, shape ``(n, 3)``.  Must lie on the
            unit sphere.
        adjacency: Adjacency list, ``adjacency[i]`` is the list of vertex
            indices adjacent to vertex ``i``.
        node_values: Per-vertex scalar values, shape ``(n,)``.
        descending: If True, flip the sign to point downhill.

    Returns:
        Tangent-plane gradient vectors, shape ``(n, 3)``.
    """
    # Build directed-edge index arrays from mesh adjacency
    source_node: np.ndarray = np.array(
        [u for u, nbs in enumerate(adjacency) for _ in nbs], dtype=np.intp
    )
    target_node: np.ndarray = np.array(
        [v for nbs in adjacency for v in nbs], dtype=np.intp
    )

    # Edge vectors in 3D
    edge_deltas: np.ndarray = positions[target_node] - positions[source_node]

    # Scalar difference across each edge
    delta: np.ndarray = node_values[target_node] - node_values[source_node]
    if descending:
        delta = -delta

    # Weight each edge vector by its scalar difference
    weighted_edges: np.ndarray = edge_deltas * delta[:, np.newaxis]

    # Accumulate into per-vertex gradient
    gradient_accumulator: np.ndarray = np.zeros(
        (len(positions), 3), dtype=np.float64
    )
    np.add.at(gradient_accumulator, source_node, weighted_edges)

    # Project out the radial component (tangent-plane on unit sphere)
    px: np.ndarray = positions[:, 0]
    py: np.ndarray = positions[:, 1]
    pz: np.ndarray = positions[:, 2]

    dot: np.ndarray = (
        gradient_accumulator[:, 0] * px
        + gradient_accumulator[:, 1] * py
        + gradient_accumulator[:, 2] * pz
    )

    return np.column_stack(
        (
            gradient_accumulator[:, 0] - dot * px,
            gradient_accumulator[:, 1] - dot * py,
            gradient_accumulator[:, 2] - dot * pz,
        )
    )

def rotate_tangent(positions: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    return np.cross(positions, vectors)

def surface_curl(positions: np.ndarray, adjacency: list[list[int]], node_values: np.ndarray) -> np.ndarray:
    vectors: np.ndarray = gradient(positions=positions, adjacency=adjacency, node_values=node_values)
    return rotate_tanget(positions=positions, vectors=vectors)
