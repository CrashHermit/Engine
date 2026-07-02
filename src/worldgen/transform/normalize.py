import numpy as np


def normalize_vectors(
    vectors: np.ndarray,
) -> np.ndarray:
    """Normalize vectors to unit length, leaving zero vectors as zero.

    Args:
        vectors: Array of vectors, shape ``(n, 3)``.

    Returns:
        Unit vectors, shape ``(n, 3)``.
    """
    magnitudes = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, magnitudes, where=magnitudes > 0)


def scale_vector_magnitudes(
    vectors: np.ndarray,
) -> np.ndarray:
    """Scale vectors so the largest magnitude maps to 1.0.

    Args:
        vectors: Array of vectors, shape ``(n, 3)``.

    Returns:
        Vectors with magnitudes in ``[0, 1]``, shape ``(n, 3)``.
    """
    magnitudes = np.linalg.norm(vectors, axis=1, keepdims=True)
    max_mag = magnitudes.max()

    if max_mag == 0:
        return vectors

    return vectors / max_mag


def interpolate_noise_array(noise_array: np.ndarray, domain: tuple) -> np.ndarray:
    min: float = noise_array.min()
    max: float = noise_array.max()

    if min == max:
        transformed_noise_array: np.ndarray = np.full_like(noise_array, domain[0])
        return transformed_noise_array

    transformed_noise_array: np.ndarray = np.interp(noise_array, (min, max), domain)
    return transformed_noise_array
