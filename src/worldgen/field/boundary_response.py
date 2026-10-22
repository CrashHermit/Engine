"""Compose nonlinear scalar responses from sparse region-pair motion."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.field.boundary_motion import (
    BoundaryMotionField,
    BoundaryMotionGradientSample,
    BoundaryMotionSample,
)
from src.worldgen.field.differential import ScalarSample, sum_indexed_scalar_samples


type BoundaryResponseSampler = Callable[[np.ndarray, BoundaryMotionSample], np.ndarray]
"""Return complete per-pair contributions, including the desired overlap weighting."""
type BoundaryResponseGradientSampler = Callable[
    [np.ndarray, BoundaryMotionGradientSample], ScalarSample
]


@dataclass(frozen=True, slots=True)
class BoundaryResponseField:
    """Sum consumer-supplied contributions without applying another influence.

    The response returns one contribution per sparse motion record. It owns
    any pair-overlap weighting; this field only reduces those contributions
    into their corresponding query positions.
    """

    motion: BoundaryMotionField
    response: BoundaryResponseSampler
    response_with_gradient: BoundaryResponseGradientSampler | None = None

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Return the summed source-space scalar response at every query."""
        source_positions = np.asarray(positions, dtype=np.float64)
        result = np.zeros(len(source_positions), dtype=np.float64)

        for start in range(0, len(source_positions), 1024):
            stop = min(start + 1024, len(source_positions))
            block = source_positions[start:stop]
            motion = self.motion.sample(block)
            result[start:stop] = self.sample_from_motion(block, motion)

        result.setflags(write=False)
        return result

    def sample_from_motion(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray:
        """Sum already-weighted pair contributions for the supplied source queries."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(motion.query_indices) == 0:
            result = np.zeros(len(query_points), dtype=np.float64)
        else:
            contributions = np.asarray(
                self.response(query_points, motion), dtype=np.float64
            )
            result = np.bincount(
                motion.query_indices,
                weights=contributions,
                minlength=len(query_points),
            )
        result.setflags(write=False)
        return result

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Reduce analytic pair contributions without probing neighboring positions."""
        query_points = np.asarray(positions, dtype=np.float64)
        values = np.empty(len(query_points), dtype=np.float64)
        gradients = np.empty((len(query_points), 3), dtype=np.float64)
        for start in range(0, len(query_points), 1024):
            stop = min(start + 1024, len(query_points))
            block = query_points[start:stop]
            sample = self.sample_from_motion_with_gradient(
                block, self.motion.sample_with_gradient(block)
            )
            values[start:stop] = sample.values
            gradients[start:stop] = sample.gradients
        return ScalarSample(values, gradients)

    def sample_from_motion_with_gradient(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample:
        """Reuse one source motion query and reduce its analytic pair responses."""
        contributions = self.response_with_gradient(positions, motion)
        return sum_indexed_scalar_samples(
            motion.sample.query_indices, contributions, len(positions)
        )
