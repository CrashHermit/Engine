"""Derived surface measurements sampled from continuous elevation."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SurfaceResult:
    """Nonnegative heights, analytic point slope, and finite-footprint shape."""

    land_height: np.ndarray
    water_depth: np.ndarray
    slope_degrees: np.ndarray
    local_relief: np.ndarray
    roughness: np.ndarray
