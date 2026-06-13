from __future__ import annotations

from collections import deque

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array, Int32Array


def _compute_boundary_intensity(*, geometry: MeshGeometry, plate_id: Int32Array, drift: Float64Array) -> tuple[Float64Array, Float64Array]:
    """Return per-cell raw collision and rift intensity on plate borders."""
    pass

def _smear_intensity(*, geometry: MeshGeometry, raw: Float64Array, belt_width: int, falloff: float) -> Float64Array:
    """Multi-source BFS smear with max-combine and per-hop falloff."""
    pass

def _sample_site_noise(*, geometry: MeshGeometry, field: FractalField, frequency: float,) -> Float64Array:
    """Sample fractal noise at every mesh site."""
    pass

def apply_boundary_uplift(*, geometry: MeshGeometry, plate_id: Int32Array, drift: Float64Array, uplift: Float64Array, config: PlatesConfig, belt_noise: FractalField, uplift_noise: FractalField, frequency: float,) -> None:
    """Add collision belts and rift seams to ``uplift`` in place."""
    pass