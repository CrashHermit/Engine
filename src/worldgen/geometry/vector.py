"""Generic Cartesian vector operations for volumetric fields."""

import numpy as np

from src.worldgen.utilities.smooth import smooth_magnitude


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
