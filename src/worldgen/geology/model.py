"""Generated geology and crust fields aligned with a spherical mesh."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from enum import IntEnum

import numpy as np

if TYPE_CHECKING:
    from src.worldgen.geology.boundary_sections import BoundarySections


class VolcanoSource(IntEnum):
    HOTSPOT = 0
    SUBDUCTION = 1
    DIVERGENCE = 2
    HISTORICAL = 3


class VolcanoState(IntEnum):
    DORMANT = 0
    ERUPTING = 1
    EXTINCT = 2


@dataclass(frozen=True, slots=True)
class VolcanoSites:
    """Unique volcano-center cells and their per-site lifecycle/geometry data."""

    cell_indices: np.ndarray
    source_types: np.ndarray
    states: np.ndarray
    supply_strength: np.ndarray
    eruption_intensity: np.ndarray
    widths_percent: np.ndarray
    heights_percent: np.ndarray


@dataclass(frozen=True, slots=True)
class VolcanismResult:
    """Potential, current activity, prospective mask, and retained volcano sites.

    Potential is a nonnegative MAX envelope of source support, used for
    candidate placement rather than asserted to be a physical magma law.
    Activity is the current eruption-intensity field and is independent of
    potential thresholding. The mask identifies threshold-qualified potential
    areas, including dormant prospective regions. Extinct historical sites are
    retained for landform reconstruction but contribute no supply or activity.
    """

    potential: np.ndarray
    activity: np.ndarray
    volcanic_mask: np.ndarray
    sites: VolcanoSites
    hotspot_potential: np.ndarray
    subduction_potential: np.ndarray
    divergence_potential: np.ndarray


@dataclass(frozen=True, slots=True)
class HotspotResult:
    seed_indices: np.ndarray
    plate_ids: np.ndarray
    widths_percent: np.ndarray
    heights_percent: np.ndarray
    potential: np.ndarray


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
    seed_indices: np.ndarray
    plate_ids: np.ndarray
    plate_rotation: np.ndarray
    plate_velocity: np.ndarray
    boundary_edge_indices: np.ndarray
    boundary_convergence: np.ndarray
    boundary_divergence: np.ndarray
    boundary_shear: np.ndarray
    boundary_sections: BoundarySections
    hotspots: HotspotResult
    crust: CrustResult
    volcanism: VolcanismResult
