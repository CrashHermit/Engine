import numpy as np

from src.worldgen.types import Float64Array


def torus_delta(
    a: Float64Array, b: Float64Array, width: float, height: float
) -> Float64Array:
    """Minimum-image displacement from ``a`` to ``b`` on a width x height torus"""
    delta: Float64Array = np.asanyarray(a=(b - a), dtype=np.float64)
    delta[0] -= width * round(number=(float(delta[0]) / width))
    delta[1] -= height * round(number=(float(delta[1]) / height))
    return delta


def torus_distance(
    a: Float64Array, b: Float64Array, width: float, height: float
) -> float:
    """Euclidean distance between two torus points using a minimum-image displacement."""
    delta: Float64Array = torus_delta(a=a, b=b, width=width, height=height)
    return float(np.linalg.norm(delta))


def torus_delta_batch(
    a: Float64Array, b: Float64Array, width: float, height: float
) -> Float64Array:
    """Vectorized ``torus_delta``: per-row minimum-image displacement ``a -> b``.

    ``a`` and ``b`` are ``(N, 2)`` arrays of points; returns an ``(N, 2)``
    array whose row ``i`` is ``torus_delta(a[i], b[i], width, height)``.
    """
    delta: Float64Array = np.asanyarray(a=(b - a), dtype=np.float64)
    delta[:, 0] -= width * np.round(delta[:, 0] / width)
    delta[:, 1] -= height * np.round(delta[:, 1] / height)
    return delta
