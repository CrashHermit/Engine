"""Transport Cartesian vectors and covectors through invertible coordinate maps.

Jacobians are indexed (query, output_axis, input_axis). Pushforward follows
that coordinate map; pullback goes in the reverse direction. Normals are unit
covectors, while scalar gradients retain their magnitude.
"""

import numpy as np


def pushforward_vectors(vectors: np.ndarray, jacobians: np.ndarray) -> np.ndarray:
    """Map input-coordinate tangent vectors into output coordinates: J v."""
    values = np.einsum("...ij,...j->...i", jacobians, vectors)
    values.setflags(write=False)
    return values


def pullback_vectors(vectors: np.ndarray, jacobians: np.ndarray) -> np.ndarray:
    """Map output-coordinate tangent vectors back: solve J v = output_vector."""
    values = np.linalg.solve(jacobians, vectors[..., None])[..., 0]
    values.setflags(write=False)
    return values


def pullback_covectors(covectors: np.ndarray, jacobians: np.ndarray) -> np.ndarray:
    """Map output-coordinate covectors to input coordinates: J transpose g."""
    values = np.einsum("...ji,...j->...i", jacobians, covectors)
    values.setflags(write=False)
    return values


def pushforward_covectors(covectors: np.ndarray, jacobians: np.ndarray) -> np.ndarray:
    """Map input-coordinate covectors forward: solve J transpose g = input."""
    values = np.linalg.solve(np.swapaxes(jacobians, -1, -2), covectors[..., None])[
        ..., 0
    ]
    values.setflags(write=False)
    return values


def pullback_normals(normals: np.ndarray, jacobians: np.ndarray) -> np.ndarray:
    """Pull back nonzero normals and restore unit length without reversing sides."""
    values = pullback_covectors(normals, jacobians)
    values = values / np.linalg.norm(values, axis=-1, keepdims=True)
    values.setflags(write=False)
    return values


def pushforward_normals(normals: np.ndarray, jacobians: np.ndarray) -> np.ndarray:
    """Push nonzero normals forward and restore unit length."""
    values = pushforward_covectors(normals, jacobians)
    values = values / np.linalg.norm(values, axis=-1, keepdims=True)
    values.setflags(write=False)
    return values


def pushforward_vector_jacobians(
    vectors: np.ndarray,
    vector_jacobians: np.ndarray,
    map_jacobians: np.ndarray,
    map_hessians: np.ndarray,
) -> np.ndarray:
    """Differentiate K v, including variation of coordinate Jacobian K."""
    leading_rank = max(
        vectors.ndim - 1,
        vector_jacobians.ndim - 2,
        map_jacobians.ndim - 2,
        map_hessians.ndim - 3,
    )
    vectors = _broadcast_pair_axis(vectors, leading_rank, 1)
    vector_jacobians = _broadcast_pair_axis(vector_jacobians, leading_rank, 2)
    map_jacobians = _broadcast_pair_axis(map_jacobians, leading_rank, 2)
    map_hessians = _broadcast_pair_axis(map_hessians, leading_rank, 3)
    values = np.einsum("...ab,...bk->...ak", map_jacobians, vector_jacobians)
    values += np.einsum("...abk,...b->...ak", map_hessians, vectors)
    values.setflags(write=False)
    return values


def pushforward_normal_jacobians(
    normals: np.ndarray,
    normal_jacobians: np.ndarray,
    map_jacobians: np.ndarray,
    map_hessians: np.ndarray,
) -> np.ndarray:
    """Differentiate normalized K^-T n with analytic map and source derivatives."""
    leading_rank = max(
        normals.ndim - 1,
        normal_jacobians.ndim - 2,
        map_jacobians.ndim - 2,
        map_hessians.ndim - 3,
    )
    normals = _broadcast_pair_axis(normals, leading_rank, 1)
    normal_jacobians = _broadcast_pair_axis(normal_jacobians, leading_rank, 2)
    map_jacobians = _broadcast_pair_axis(map_jacobians, leading_rank, 2)
    map_hessians = _broadcast_pair_axis(map_hessians, leading_rank, 3)
    raw = pushforward_covectors(normals, map_jacobians)
    raw_length = np.linalg.norm(raw, axis=-1, keepdims=True)
    unit = raw / raw_length
    map_term = np.einsum("...aik,...a->...ik", map_hessians, raw)
    raw_jacobians = np.linalg.solve(
        np.swapaxes(map_jacobians, -1, -2), normal_jacobians - map_term
    )
    projector = np.eye(3) - unit[..., :, None] * unit[..., None, :]
    values = np.einsum(
        "...ij,...jk->...ik",
        projector / raw_length[..., None],
        raw_jacobians,
    )
    values.setflags(write=False)
    return values


def _broadcast_pair_axis(values: np.ndarray, leading_rank: int, trailing_rank: int):
    while values.ndim - trailing_rank < leading_rank:
        values = np.expand_dims(values, axis=values.ndim - trailing_rank)
    return values
