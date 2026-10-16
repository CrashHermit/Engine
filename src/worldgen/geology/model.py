"""Generated geology and crust fields aligned with a spherical mesh."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.worldgen.geology.boundary_sections import BoundarySections


@dataclass(frozen=True, slots=True)
class CrustResult:
    region_ids: np.ndarray
    seed_indices: np.ndarray
    continental_regions: np.ndarray
    continental_mask: np.ndarray
    shaping_field: np.ndarray
    effective_density: np.ndarray
    density_anomaly: np.ndarray
    region_effective_density: np.ndarray


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
    boundary_sections: BoundarySections
    crust: CrustResult
