"""Dense scalar fields derived independently from sparse region motion."""

from dataclasses import dataclass

import numpy as np
from src.worldgen.field.differential import ScalarSample, sum_indexed_scalar_samples

from src.worldgen.field.boundary_motion import (
    BoundaryMotionField,
    BoundaryMotionGradientSample,
    BoundaryMotionSample,
)


@dataclass(frozen=True, slots=True)
class InteractionSample:
    """Influence-weighted convergence, divergence and shear at each query."""

    convergence: np.ndarray
    divergence: np.ndarray
    shear: np.ndarray


@dataclass(frozen=True, slots=True)
class InteractionGradientSample:
    """Independently accessible dense interaction values and Cartesian gradients."""

    convergence: ScalarSample
    divergence: ScalarSample
    shear: ScalarSample


@dataclass(frozen=True, slots=True)
class BoundaryInteractionField:
    """Expose independent continuous scalar fields for region interactions."""

    motion: BoundaryMotionField

    def sample(self, positions: np.ndarray) -> InteractionSample:
        """Sum each nonnegative pair component independently at each query."""
        source_positions = np.asarray(positions, dtype=np.float64)
        convergence = np.zeros(len(source_positions), dtype=np.float64)
        divergence = np.zeros(len(source_positions), dtype=np.float64)
        shear = np.zeros(len(source_positions), dtype=np.float64)

        for start in range(0, len(source_positions), 1024):
            stop = min(start + 1024, len(source_positions))
            sample = self.motion.sample(source_positions[start:stop])
            result = self.sample_from_motion(stop - start, sample)
            convergence[start:stop] = result.convergence
            divergence[start:stop] = result.divergence
            shear[start:stop] = result.shear

        for values in (convergence, divergence, shear):
            values.setflags(write=False)
        return InteractionSample(
            convergence=convergence,
            divergence=divergence,
            shear=shear,
        )

    def sample_from_motion(
        self, query_count: int, motion: BoundaryMotionSample
    ) -> InteractionSample:
        """Reduce weighted pair channels for an already evaluated motion sample."""
        convergence = np.bincount(
            motion.query_indices,
            weights=motion.influence * motion.convergence,
            minlength=query_count,
        )
        divergence = np.bincount(
            motion.query_indices,
            weights=motion.influence * motion.divergence,
            minlength=query_count,
        )
        shear = np.bincount(
            motion.query_indices,
            weights=motion.influence * motion.shear,
            minlength=query_count,
        )
        for values in (convergence, divergence, shear):
            values.setflags(write=False)
        return InteractionSample(
            convergence=convergence,
            divergence=divergence,
            shear=shear,
        )

    def sample_convergence(self, positions: np.ndarray) -> np.ndarray:
        """Sample the influence-weighted convergence scalar field."""
        return self.sample(positions).convergence

    def sample_divergence(self, positions: np.ndarray) -> np.ndarray:
        """Sample the influence-weighted divergence scalar field."""
        return self.sample(positions).divergence

    def sample_shear(self, positions: np.ndarray) -> np.ndarray:
        """Sample the influence-weighted shear scalar field."""
        return self.sample(positions).shear

    def sample_with_gradient(self, positions: np.ndarray) -> InteractionGradientSample:
        """Reuse one motion query per block for all three analytic scalar fields."""
        points = np.asarray(positions, dtype=np.float64)
        convergence = np.empty(len(points), dtype=np.float64)
        divergence = np.empty(len(points), dtype=np.float64)
        shear = np.empty(len(points), dtype=np.float64)
        convergence_gradients = np.empty((len(points), 3), dtype=np.float64)
        divergence_gradients = np.empty((len(points), 3), dtype=np.float64)
        shear_gradients = np.empty((len(points), 3), dtype=np.float64)
        for start in range(0, len(points), 1024):
            stop = min(start + 1024, len(points))
            motion = self.motion.sample_with_gradient(points[start:stop])
            result = self.sample_from_motion_with_gradient(stop - start, motion)
            convergence[start:stop] = result.convergence.values
            divergence[start:stop] = result.divergence.values
            shear[start:stop] = result.shear.values
            convergence_gradients[start:stop] = result.convergence.gradients
            divergence_gradients[start:stop] = result.divergence.gradients
            shear_gradients[start:stop] = result.shear.gradients
        return InteractionGradientSample(
            ScalarSample(convergence, convergence_gradients),
            ScalarSample(divergence, divergence_gradients),
            ScalarSample(shear, shear_gradients),
        )

    def sample_from_motion_with_gradient(
        self, query_count: int, motion: BoundaryMotionGradientSample
    ) -> InteractionGradientSample:
        """Reduce shared sparse motion gradients without repeating ownership queries."""
        sample = motion.sample

        def reduce_channel(values: np.ndarray, gradients: np.ndarray) -> ScalarSample:
            weighted = ScalarSample(
                sample.influence * values,
                sample.influence[:, None] * gradients
                + values[:, None] * motion.influence_gradients,
            )
            return sum_indexed_scalar_samples(
                sample.query_indices, weighted, query_count
            )

        return InteractionGradientSample(
            convergence=reduce_channel(
                sample.convergence, motion.convergence_gradients
            ),
            divergence=reduce_channel(sample.divergence, motion.divergence_gradients),
            shear=reduce_channel(sample.shear, motion.shear_gradients),
        )

    def sample_convergence_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        return self.sample_with_gradient(positions).convergence

    def sample_divergence_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        return self.sample_with_gradient(positions).divergence

    def sample_shear_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        return self.sample_with_gradient(positions).shear
