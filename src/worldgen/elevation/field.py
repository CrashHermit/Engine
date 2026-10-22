"""Continuous source-space coastal and tectonic elevation composition."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.model import (
    SourceElevationGradientSample,
    SourceElevationSample,
)
from src.worldgen.elevation.source_coastal import SourceCoastalField
from src.worldgen.elevation.tectonic_response import TectonicResponseSampler
from src.worldgen.elevation.volcanism import VolcanicField
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.field.differential import ScalarSample, sum_indexed_scalar_samples
from src.worldgen.geology.field import GeologyField
from src.worldgen.geology.model import GeologyGradientSample, GeologySample


@dataclass(frozen=True, slots=True)
class SourceElevationField:
    """Evaluate coastal, volcanic, and named tectonic relief in source space."""

    geology: GeologyField
    coastal: SourceCoastalField
    volcanism: VolcanicField
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
        geology_sample: GeologySample | None = None,
    ) -> SourceElevationSample:
        """Reuse same-query geological inputs for all relief components."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(query_points) == 0:
            return _empty_source_elevation_sample()
        sample = (
            self.geology.sample_source(query_points)
            if geology_sample is None
            else geology_sample
        )
        ridge_weights = (
            self.sampler.ridge_detail.sample(query_points)[sample.motion.query_indices]
            if self.sampler.ridge_detail is not None
            else None
        )
        pair_response = self.sampler.sample_from_context(
            sample.context, ridge_weights=ridge_weights
        )
        indices = sample.motion.query_indices
        query_count = len(query_points)
        convergent = _reduce_pair_response(
            indices, pair_response.convergent, query_count
        )
        divergent = _reduce_pair_response(indices, pair_response.divergent, query_count)
        transform = _reduce_pair_response(indices, pair_response.transform, query_count)
        shear = _reduce_pair_response(indices, pair_response.shear, query_count)
        tectonic = _reduce_pair_response(indices, pair_response.total, query_count)
        coastal = self.coastal.sample_from_weight(
            query_points, sample.result.continental_weight
        ).elevation
        volcanic = self.volcanism.sample(query_points, geology_sample=sample)
        total = coastal + tectonic + volcanic.relief
        arrays = (
            coastal,
            volcanic.potential,
            volcanic.strength,
            volcanic.relief,
            convergent,
            divergent,
            transform,
            shear,
            tectonic,
            total,
        )
        for values in arrays:
            values.setflags(write=False)
        return SourceElevationSample(
            coastal_elevation=coastal,
            volcanic_potential=volcanic.potential,
            volcanic_strength=volcanic.strength,
            volcanic_relief=volcanic.relief,
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
        geology_sample: GeologyGradientSample | None = None,
    ) -> SourceElevationGradientSample:
        """Compose every source contribution from shared analytic geological inputs."""
        query_points = np.asarray(positions, dtype=np.float64)
        sample = (
            self.geology.sample_source_with_gradient(query_points)
            if geology_sample is None
            else geology_sample
        )
        indices = sample.sample.motion.query_indices
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
                sample.sample.result.continental_weight,
                sample.continental_weight_gradients,
            ),
        )
        volcanic = self.volcanism.sample_with_gradient(
            query_points, geology_sample=sample
        )
        total = ScalarSample(
            coastal.values + tectonic.values + volcanic.relief.values,
            coastal.gradients + tectonic.gradients + volcanic.relief.gradients,
        )
        return SourceElevationGradientSample(
            coastal_elevation=coastal,
            volcanic_potential=volcanic.potential,
            volcanic_strength=volcanic.strength,
            volcanic_relief=volcanic.relief,
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


def _empty_source_elevation_sample() -> SourceElevationSample:
    empty = np.empty(0, dtype=np.float64)
    empty.setflags(write=False)
    return SourceElevationSample(
        coastal_elevation=empty,
        volcanic_potential=empty,
        volcanic_strength=empty,
        volcanic_relief=empty,
        convergent_relief=empty,
        divergent_relief=empty,
        transform_relief=empty,
        shear_relief=empty,
        tectonic_relief=empty,
        total=empty,
    )
