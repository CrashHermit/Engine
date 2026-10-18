"""Sampled elevation components and geographic metadata."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class CoastalResult:
    elevation: np.ndarray
    margin_distance: np.ndarray


@dataclass(frozen=True, slots=True)
class ElevationResult:
    coastal_elevation: np.ndarray
    tectonic_relief: np.ndarray
    volcanic_relief: np.ndarray
    impact_relief: np.ndarray
    terrain_variation: np.ndarray
    elevation: np.ndarray
    margin_distance: np.ndarray
    crust_boundary_edge_indices: np.ndarray
    elevation_range_m: tuple[float, float]
    coastal_elevation_range_m: tuple[float, float]
