"""Generated coastal terrain fields."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class TerrainResult:
    margin_distance: np.ndarray
    base_elevation: np.ndarray
    land_mask: np.ndarray
    coast_edge_indices: np.ndarray
    elevation_range_m: tuple[float, float]
