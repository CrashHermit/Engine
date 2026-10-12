"""Scalar and vector remapping helpers."""

import numpy as np


def interpolate_values(values: np.ndarray, domain: tuple[float, float]) -> np.ndarray:
    """Affine-remap values from their observed range to a target domain."""
    values_min = values.min()
    values_max = values.max()
    normalized = (values - values_min) / (values_max - values_min)
    return normalized * (domain[1] - domain[0]) + domain[0]


def scale_vector_magnitudes(vectors: np.ndarray) -> np.ndarray:
    """Scale all vector magnitudes by the largest magnitude."""
    magnitudes = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / magnitudes.max()
