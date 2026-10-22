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
