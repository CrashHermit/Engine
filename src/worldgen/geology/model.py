"""Generated geology and crust fields aligned with a spherical mesh."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class CrustResult:
    region_ids: np.ndarray
    seed_indices: np.ndarray
    continental_regions: np.ndarray
    continental_mask: np.ndarray
    shaping_field: np.ndarray


@dataclass(frozen=True, slots=True)
class PlateResult:
    seed_indices: np.ndarray
    plate_ids: np.ndarray
    plate_rotation: np.ndarray
    plate_velocity: np.ndarray
    boundary_edge_indices: np.ndarray


@dataclass(frozen=True, slots=True)
class GeologyResult:
    magma_intensity: np.ndarray
    seed_indices: np.ndarray
    plate_ids: np.ndarray
    magma_velocity: np.ndarray
    plate_rotation: np.ndarray
    plate_velocity: np.ndarray
    boundary_edge_indices: np.ndarray
    boundary_convergence: np.ndarray
    boundary_divergence: np.ndarray
    boundary_shear: np.ndarray
    crust: CrustResult
