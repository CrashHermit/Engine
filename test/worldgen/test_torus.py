"""Torus geometry helpers."""

from __future__ import annotations

import numpy as np

from src.worldgen.geometry.torus import torus_delta, torus_distance
from src.worldgen.types import Float64Array

WIDTH: float = 100.0
HEIGHT: float = 100.0


def test_torus_delta_wraps_short_way_across_seam() -> None:
    """A point just past the east edge wraps to the west side."""
    a: Float64Array = np.array([95.0, 50.0], dtype=np.float64)
    b: Float64Array = np.array([5.0, 50.0], dtype=np.float64)
    delta: Float64Array = torus_delta(a=a, b=b, width=WIDTH, height=HEIGHT)
    assert delta[0] == 10.0
    assert delta[1] == 0.0
    assert torus_distance(a=a, b=b, width=WIDTH, height=HEIGHT) == 10.0