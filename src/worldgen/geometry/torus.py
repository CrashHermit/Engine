from __future__ import annotations

import numpy as np

from src.worldgen.types import Float64Array


def torus_delta(a: Float64Array, b: Float64Array, width: float, height: float) -> Float64Array:
    """Minimum-image displacement from ``a`` to ``b`` on a width x height torus"""
    delta: Float64Array = np.asanyarray(a=(b - a), dtype=np.float64)
    delta[0] -= width * round(number=(float(delta[0]) / width))
    delta[1] -= height * round(number=(float(delta[1]) / height))
    return delta

def torus_distance(a: Float64Array, b: Float64Array, width: float, height: float) -> float:
    """Euclidean distance between two torus points using a minimum-image displacement."""
    delta: Float64Array = torus_delta(a=a, b=b, width=width, height=height)
    return float(np.linalg.norm(delta))
