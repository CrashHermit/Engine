"""Continuous geological values and per-query interaction metadata."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.boundary_motion import (
    BoundaryMotionGradientSample,
    BoundaryMotionSample,
)
from src.worldgen.geology.tectonic_context import (
    TectonicContextGradientSample,
    TectonicContextSample,
)


@dataclass(frozen=True, slots=True)
class GeologyResult:
    """Dense discrete ownership and continuous geology channels."""

    plate_ids: np.ndarray
    crust_region_ids: np.ndarray
    continental_mask: np.ndarray
    continental_weight: np.ndarray
    subduction_preference_strength: np.ndarray
    max_plate_weight: np.ndarray
    region_overlap: np.ndarray
    convergence: np.ndarray
    divergence: np.ndarray
    shear: np.ndarray


@dataclass(frozen=True, slots=True)
class GeologySample:
    """Dense geology plus sparse pair data for same-query elevation responses."""

    result: GeologyResult
    motion: BoundaryMotionSample
    context: TectonicContextSample


@dataclass(frozen=True, slots=True)
class GeologyGradientSample:
    sample: GeologySample
    motion: BoundaryMotionGradientSample
    context: TectonicContextGradientSample
    continental_weight_gradients: np.ndarray

    def __post_init__(self) -> None:
        self.continental_weight_gradients.setflags(write=False)
