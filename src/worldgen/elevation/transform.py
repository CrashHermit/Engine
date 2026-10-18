"""Continuous signed transform relief profiles."""

import numpy as np
from numba.extending import register_jitable

from src.worldgen.elevation.profiles import transform_profile


def transform_strength(normal: np.ndarray, shear: np.ndarray) -> np.ndarray:
    """Return signed normal/shear motion strength, with zero for a zero denominator."""
    denominator = np.abs(normal) + shear
    valid = denominator != 0.0
    strength = np.zeros_like(denominator, dtype=np.float64)
    strength[valid] = normal[valid] * shear[valid] / denominator[valid]
    return strength


@register_jitable
def transform_value(distance, parameters, peak):
    """Evaluate compact signed relief without temporary arrays."""
    width, height = parameters
    if distance >= width:
        return 0.0
    return transform_profile(distance, width) * peak * height
