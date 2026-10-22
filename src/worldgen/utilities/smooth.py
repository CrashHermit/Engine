"""Closed-form smooth extrema and magnitudes for continuous scalar fields."""

import numpy as np
from scipy.special import logsumexp


def smooth_maximum(
    first: np.ndarray | float,
    second: np.ndarray | float,
    *,
    width: float,
) -> np.ndarray:
    """Return a stable log-sum-exp approximation of ``max(first, second)``.

    ``width`` is the transition scale. Positive widths produce an analytic
    approximation; the exact maximum is recovered only in the zero-width
    limit.
    """
    first_values, second_values = np.broadcast_arrays(
        np.asarray(first, dtype=np.float64),
        np.asarray(second, dtype=np.float64),
    )
    scaled = np.stack((first_values / width, second_values / width), axis=0)
    return np.asarray(width * logsumexp(scaled, axis=0), dtype=np.float64)


def smooth_minimum(
    first: np.ndarray | float,
    second: np.ndarray | float,
    *,
    width: float,
) -> np.ndarray:
    """Return a stable log-sum-exp approximation of ``min(first, second)``."""
    return -smooth_maximum(-np.asarray(first), -np.asarray(second), width=width)


def smooth_magnitude(
    squared_magnitude: np.ndarray, *, smoothing: float = 0.01
) -> np.ndarray:
    """Return a zero-preserving smooth norm from a squared norm and positive scale."""
    squared = np.asarray(squared_magnitude, dtype=np.float64)
    return squared / (np.sqrt(squared + smoothing * smoothing) + smoothing)
