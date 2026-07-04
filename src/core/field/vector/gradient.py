"""Gradient of a scalar field over a mesh on the unit sphere."""

import numpy as np


def gradient(
    positions: np.ndarray,
    neighbors: list[list[int]],
    values: np.ndarray,
    descending: bool = False,
) -> np.ndarray:
    """Per-vertex gradient of a scalar field on a unit-sphere mesh.

    Computes the tangent-plane gradient by accumulating weighted edge
    vectors and projecting the radial component out.

    Args:
        positions: Vertex positions, shape ``(n, 3)``.  Must lie on the
            unit sphere.
        neighbors: Adjacency list, ``neighbors[i]`` is the list of vertex
            indices adjacent to vertex ``i``.
        values: Per-vertex scalar values, shape ``(n,)``.
        descending: If True, flip the sign to point downhill.

    Returns:
        Tangent-plane gradient vectors, shape ``(n, 3)``.
    """
    # Build directed-edge index arrays from mesh adjacency
    source_idx: np.ndarray = np.array(
        [u for u, nbs in enumerate(neighbors) for _ in nbs], dtype=np.intp
    )
    target_idx: np.ndarray = np.array(
        [v for nbs in neighbors for v in nbs], dtype=np.intp
    )

    # Edge vectors in 3D
    edge_deltas: np.ndarray = positions[target_idx] - positions[source_idx]

    # Scalar difference across each edge
    delta: np.ndarray = values[target_idx] - values[source_idx]
    if descending:
        delta = -delta

    # Weight each edge vector by its scalar difference
    weighted_edges: np.ndarray = edge_deltas * delta[:, np.newaxis]

    # Accumulate into per-vertex gradient
    v: np.ndarray = np.zeros((len(positions), 3), dtype=np.float64)
    np.add.at(v, source_idx, weighted_edges)

    # Project out the radial component (tangent-plane on unit sphere)
    px: np.ndarray = positions[:, 0]
    py: np.ndarray = positions[:, 1]
    pz: np.ndarray = positions[:, 2]

    dot: np.ndarray = v[:, 0] * px + v[:, 1] * py + v[:, 2] * pz

    return np.column_stack(
        (
            v[:, 0] - dot * px,
            v[:, 1] - dot * py,
            v[:, 2] - dot * pz,
        )
    )
