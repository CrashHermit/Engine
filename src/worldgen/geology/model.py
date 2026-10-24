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
class SourceReliefInputs:
    """Dense material weights and sparse, source-parameterized response inputs."""

    continental_weight: np.ndarray
    query_indices: np.ndarray
    context: TectonicContextSample

    def __post_init__(self) -> None:
        self.continental_weight.setflags(write=False)
        self.query_indices.setflags(write=False)


@dataclass(frozen=True, slots=True)
class SourceReliefGradientInputs:
    """Response inputs with gradients relative to source XYZ coordinates."""

    continental_weight: np.ndarray
    continental_weight_gradients: np.ndarray
    query_indices: np.ndarray
    context: TectonicContextGradientSample

    def __post_init__(self) -> None:
        self.continental_weight.setflags(write=False)
        self.continental_weight_gradients.setflags(write=False)
        self.query_indices.setflags(write=False)


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
    """Dense geology plus sparse pair data for same-query relief responses."""

    result: GeologyResult
    motion: BoundaryMotionSample
    context: TectonicContextSample

    def to_relief_inputs(self) -> SourceReliefInputs:
        """Project shared arrays without copying or reinterpreting geology."""
        return SourceReliefInputs(
            self.result.continental_weight, self.motion.query_indices, self.context
        )


@dataclass(frozen=True, slots=True)
class GeologyGradientSample:
    sample: GeologySample
    motion: BoundaryMotionGradientSample
    context: TectonicContextGradientSample
    continental_weight_gradients: np.ndarray

    def __post_init__(self) -> None:
        self.continental_weight_gradients.setflags(write=False)

    def to_relief_inputs(self) -> SourceReliefGradientInputs:
        """Project shared source-coordinate values and gradients without copies."""
        return SourceReliefGradientInputs(
            self.sample.result.continental_weight,
            self.continental_weight_gradients,
            self.sample.motion.query_indices,
            self.context,
        )
