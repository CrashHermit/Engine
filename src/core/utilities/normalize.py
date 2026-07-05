"""Vector and scalar normalization utilities."""

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


def interpolate_values(values: np.ndarray, domain: tuple) -> np.ndarray:
    """Remap values from their current range to a target domain.

    Args:
        values: Input values, shape ``(n,)``.
        domain: Target ``(low, high)`` range to remap to.

    Returns:
        Remapped values, shape ``(n,)``.
    """

    low = domain[0]
    high = domain[1]

    values_min = values.min()
    values_max = values.max()

    if values_max == values_min:
        return np.full_lie(values, low)

    normalized = (values - values_min) / (values_max - values_min)

    interpolated_values = normalized * (high - low) + low

    return interpolated_values
