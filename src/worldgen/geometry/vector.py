"""Generic Cartesian vector operations for volumetric fields."""

import numpy as np

from src.worldgen.utilities.smooth import smooth_magnitude


def regularized_normalize(
    vectors: np.ndarray, smoothing: float, *, multiplier: np.ndarray | float = 1.0
) -> np.ndarray:
    """Normalize vectors with a smooth denominator and optional numerator scale."""
    values = np.asarray(vectors, dtype=np.float64)
    denominator = np.sqrt(np.einsum("ij,ij->i", values, values) + smoothing * smoothing)
    result = multiplier * values / denominator[:, None]
    result.setflags(write=False)
    return result


def regularized_normalize_with_jacobian(
    vectors: np.ndarray, smoothing: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return normalized vectors and derivatives with respect to input vectors."""
    values = np.asarray(vectors, dtype=np.float64)
    squared = np.einsum("ij,ij->i", values, values)
    denominator = np.sqrt(squared + smoothing * smoothing)
    inverse = 1.0 / denominator
    normalized = values * inverse[:, None]
    identity = np.broadcast_to(np.eye(3), (len(values), 3, 3))
    jacobian = (
        identity * inverse[:, None, None]
        - values[:, :, None] * values[:, None, :] * inverse[:, None, None] ** 3
    )
    normalized.setflags(write=False)
    jacobian.setflags(write=False)
    return normalized, jacobian


def relative_motion_components(
    first: np.ndarray,
    second: np.ndarray,
    normals: np.ndarray,
    *,
    shear_smoothing: float = 0.01,
) -> tuple[np.ndarray, np.ndarray]:
    """Return signed normal opening and zero-preserving smooth tangent magnitude."""

    relative = np.asarray(second, dtype=np.float64) - np.asarray(
        first, dtype=np.float64
    )
    boundary_normals = np.asarray(normals, dtype=np.float64)
    opening = np.einsum("ij,ij->i", relative, boundary_normals)
    sliding_vectors = relative - opening[:, None] * boundary_normals
    sliding_squared = np.einsum("ij,ij->i", sliding_vectors, sliding_vectors)
    sliding = smooth_magnitude(sliding_squared, smoothing=shear_smoothing)
    opening.setflags(write=False)
    sliding.setflags(write=False)
    return opening, sliding
