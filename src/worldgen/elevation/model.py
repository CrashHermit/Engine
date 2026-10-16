"""Generated coastal elevation fields."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ElevationResult:
    base_elevation: np.ndarray
    tectonic_relief: np.ndarray
    elevation: np.ndarray
    margin_distance: np.ndarray
    land_mask: np.ndarray
    crust_boundary_edge_indices: np.ndarray
    elevation_range_m: tuple[float, float]
    base_elevation_range_m: tuple[float, float]
