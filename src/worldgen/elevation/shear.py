"""Pure-shear fault-zone relief responses."""

import numpy as np
from numba.extending import register_jitable

from src.worldgen.elevation.profiles import shear_profile


@register_jitable
def shear_component(normal, shear):
    """Return the shear strength left after the oblique transform component."""
    denominator = abs(normal) + shear
    return shear * shear / denominator if denominator != 0.0 else 0.0


def shear_strength(normal: np.ndarray, shear: np.ndarray) -> np.ndarray:
    """Return the shear component not already assigned to oblique transform relief."""
    denominator = np.abs(normal) + shear
    valid = denominator != 0.0
    strength = np.zeros_like(denominator, dtype=np.float64)
    strength[valid] = shear[valid] * shear[valid] / denominator[valid]
    return strength


@register_jitable
def shear_value(distance, parameters, peak):
    """Evaluate compact pure-shear relief without temporary arrays."""
    width, height = parameters
    if distance >= width:
        return 0.0
    return shear_profile(distance, width) * peak * height
