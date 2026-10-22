"""Pure-shear fault-zone relief responses."""

import numpy as np
from numba.extending import register_jitable

from src.worldgen.elevation.profiles import shear_profile


def shear_strength(
    normal: np.ndarray, shear: np.ndarray, *, smoothing: float
) -> np.ndarray:
    """Return nonnegative shear response with a smoothed normal magnitude."""
    denominator = np.sqrt(normal * normal + smoothing * smoothing) + shear
    return shear * shear / denominator


@register_jitable
def shear_value(distance, parameters, peak):
    """Evaluate compact pure-shear relief without temporary arrays."""
    width, height = parameters
    if distance >= width:
        return 0.0
    return shear_profile(distance, width) * peak * height
