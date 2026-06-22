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


def torus_point_segment(
    *,
    p: Float64Array,
    a: Float64Array,
    b: Float64Array,
    width: float,
    height: float,
) -> tuple[float, float]:
    """Return ``(distance, t)`` from point ``p`` to segment ``a -> b`` on the torus.

    Works in minimum-image space relative to ``a``: project ``p`` onto the
    segment line, clamp the projection parameter ``t`` to ``[0, 1]``, and
    measure the distance to that clamped closest point.

    Args:
        p: Query point ``(x, y)``.
        a: Segment start ``(x, y)``.
        b: Segment end ``(x, y)``.
        width: Torus width.
        height: Torus height.

    Returns:
        ``(distance, t)`` where ``t`` in ``[0, 1]`` locates the closest point
        along ``a -> b``.
    """
    ab: Float64Array = torus_delta(a=a, b=b, width=width, height=height)
    ap: Float64Array = torus_delta(a=a, b=p, width=width, height=height)
    ab_len2: float = float(ab[0] * ab[0] + ab[1] * ab[1])

    if ab_len2 < 1e-12:
        # Degenerate segment: distance to the single endpoint.
        return float(np.hypot(ap[0], ap[1])), 0.0

    t: float = float(np.clip((ap[0] * ab[0] + ap[1] * ab[1]) / ab_len2, 0.0, 1.0))
    closest_x: float = float(ap[0] - t * ab[0])
    closest_y: float = float(ap[1] - t * ab[1])
    return float(np.hypot(closest_x, closest_y)), t
