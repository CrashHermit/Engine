"""Source-parameterized relief composition with world-oriented interactions."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.relief.model import (
    SourceReliefGradientSample,
    SourceReliefSample,
)
from src.worldgen.relief.coastal import SourceCoastalField
from src.worldgen.relief.tectonic_response import TectonicResponseSampler
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.differential import ScalarSample, sum_indexed_scalar_samples
from src.worldgen.geology.model import SourceReliefGradientInputs, SourceReliefInputs


@dataclass(frozen=True, slots=True)
class SourceReliefField:
    """Query relief at source coordinates using transported geological motion."""

    sample_relief_inputs: Callable[[np.ndarray], SourceReliefInputs]
    sample_relief_inputs_with_gradient: Callable[
        [np.ndarray], SourceReliefGradientInputs
    ]
    coastal: SourceCoastalField
    sampler: TectonicResponseSampler
    tectonic: BoundaryResponseField
    convergent: BoundaryResponseField
    divergent: BoundaryResponseField
    transform: BoundaryResponseField
    shear: BoundaryResponseField

    def sample_source(
        self,
        positions: np.ndarray,
        *,
        relief_inputs: SourceReliefInputs | None = None,
    ) -> SourceReliefSample:
        """Reuse same-query geological inputs for all relief components."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(query_points) == 0:
            return _empty_source_relief_sample()
        sample = (
            self.sample_relief_inputs(query_points)
            if relief_inputs is None
            else relief_inputs
        )
        ridge_weights = (
            self.sampler.ridge_detail.sample(query_points)[sample.query_indices]
            if self.sampler.ridge_detail is not None
            else None
        )
        pair_response = self.sampler.sample_from_context(
            sample.context, ridge_weights=ridge_weights
        )
        indices = sample.query_indices
        query_count = len(query_points)
        convergent = _reduce_pair_response(
            indices, pair_response.convergent, query_count
        )
        divergent = _reduce_pair_response(indices, pair_response.divergent, query_count)
        transform = _reduce_pair_response(indices, pair_response.transform, query_count)
        shear = _reduce_pair_response(indices, pair_response.shear, query_count)
        tectonic = _reduce_pair_response(indices, pair_response.total, query_count)
        coastal = self.coastal.sample_from_weight(
            query_points, sample.continental_weight
        ).elevation
        total = coastal + tectonic
        arrays = (
            coastal,
            convergent,
            divergent,
            transform,
            shear,
            tectonic,
            total,
        )
        for values in arrays:
            values.setflags(write=False)
        return SourceReliefSample(
            coastal_elevation=coastal,
            convergent_relief=convergent,
            divergent_relief=divergent,
            transform_relief=transform,
            shear_relief=shear,
            tectonic_relief=tectonic,
            total=total,
        )

    def sample_total_source(self, positions: np.ndarray) -> np.ndarray:
        """Sample only total source elevation in bounded query blocks."""
        query_points = np.asarray(positions, dtype=np.float64)
        total = np.empty(len(query_points), dtype=np.float64)
        for start in range(0, len(query_points), 1024):
            stop = min(start + 1024, len(query_points))
            total[start:stop] = self.sample_source(query_points[start:stop]).total
        total.setflags(write=False)
        return total

    def sample_source_with_gradient(
        self,
        positions: np.ndarray,
        *,
        relief_inputs: SourceReliefGradientInputs | None = None,
    ) -> SourceReliefGradientSample:
        """Compose every source contribution from shared analytic geological inputs."""
        query_points = np.asarray(positions, dtype=np.float64)
        sample = (
            self.sample_relief_inputs_with_gradient(query_points)
            if relief_inputs is None
            else relief_inputs
        )
        indices = sample.query_indices
        ridge_weights = None
        if self.sampler.ridge_detail is not None:
            ridge = self.sampler.ridge_detail.sample_with_gradient(query_points)
            ridge_weights = ScalarSample(
                ridge.values[indices], ridge.gradients[indices]
            )
        pair_response = self.sampler.sample_from_context_with_gradient(
            sample.context, ridge_weights=ridge_weights
        )
        query_count = len(query_points)
        convergent = sum_indexed_scalar_samples(
            indices, pair_response.convergent, query_count
        )
        divergent = sum_indexed_scalar_samples(
            indices, pair_response.divergent, query_count
        )
        transform = sum_indexed_scalar_samples(
            indices, pair_response.transform, query_count
        )
        shear = sum_indexed_scalar_samples(indices, pair_response.shear, query_count)
        tectonic = sum_indexed_scalar_samples(indices, pair_response.total, query_count)
        coastal = self.coastal.sample_from_weight_with_gradient(
            query_points,
            ScalarSample(
                sample.continental_weight,
                sample.continental_weight_gradients,
            ),
        )
        total = ScalarSample(
            coastal.values + tectonic.values,
            coastal.gradients + tectonic.gradients,
        )
        return SourceReliefGradientSample(
            coastal_elevation=coastal,
            convergent_relief=convergent,
            divergent_relief=divergent,
            transform_relief=transform,
            shear_relief=shear,
            tectonic_relief=tectonic,
            total=total,
        )

    def sample_total_source_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Sample total source elevation and XYZ gradients in bounded query blocks."""
        query_points = np.asarray(positions, dtype=np.float64)
        values = np.empty(len(query_points), dtype=np.float64)
        gradients = np.empty((len(query_points), 3), dtype=np.float64)
        for start in range(0, len(query_points), 1024):
            stop = min(start + 1024, len(query_points))
            sample = self.sample_source_with_gradient(query_points[start:stop]).total
            values[start:stop] = sample.values
            gradients[start:stop] = sample.gradients
        return ScalarSample(values, gradients)


def _reduce_pair_response(
    query_indices: np.ndarray, values: np.ndarray, query_count: int
) -> np.ndarray:
    """Sum sparse pair contributions into their original query positions."""
    reduced = np.bincount(query_indices, weights=values, minlength=query_count)
    return np.asarray(reduced, dtype=np.float64)


def _empty_source_relief_sample() -> SourceReliefSample:
    empty = np.empty(0, dtype=np.float64)
    empty.setflags(write=False)
    return SourceReliefSample(
        coastal_elevation=empty,
        convergent_relief=empty,
        divergent_relief=empty,
        transform_relief=empty,
        shear_relief=empty,
        tectonic_relief=empty,
        total=empty,
    )
