"""Continuous signed transform relief profiles."""

import numpy as np
from numba.extending import register_jitable

from src.worldgen.elevation.profiles import transform_profile


def transform_strength(
    normal: np.ndarray, shear: np.ndarray, *, smoothing: float
) -> np.ndarray:
    """Return signed normal/shear response with a smoothed normal magnitude."""
    denominator = np.sqrt(normal * normal + smoothing * smoothing) + shear
    return normal * shear / denominator


@register_jitable
def transform_value(distance, parameters, peak):
    """Evaluate compact signed relief without temporary arrays."""
    width, height = parameters
    if distance >= width:
        return 0.0
    return transform_profile(distance, width) * peak * height
