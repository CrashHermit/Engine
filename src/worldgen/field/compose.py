"""Generic composition of world-coordinate transforms and scalar fields."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import (
    ScalarGradientSampler,
    ScalarSample,
    VectorHessianSampler,
    VectorJacobianSampler,
    VectorSample,
)
from src.worldgen.geometry.differential import (
    pullback_covectors,
    pullback_normals,
    pullback_vectors,
    pushforward_vector_jacobians,
    pushforward_vectors,
)

type CoordinateTransform = Callable[[np.ndarray], np.ndarray]
type ScalarSampler = Callable[[np.ndarray], np.ndarray]
type VectorSampler = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True, slots=True)
class WarpedScalarField:
    """Sample a scalar source field after transforming its query coordinates."""

    transform: CoordinateTransform
    sample_source: ScalarSampler
    transform_with_jacobian: VectorJacobianSampler | None = None
    sample_source_with_gradient: ScalarGradientSampler | None = None

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Evaluate the source scalar field at transformed world positions."""
        world_positions = np.asarray(positions, dtype=np.float64)
        source_positions = self.transform(world_positions)
        return self.sample_source(source_positions)

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Pull a source gradient back with J transpose, without normalizing it."""
        transformed = self.transform_with_jacobian(
            np.asarray(positions, dtype=np.float64)
        )
        source = self.sample_source_with_gradient(transformed.values)
        return ScalarSample(
            source.values, pullback_covectors(source.gradients, transformed.jacobians)
        )


@dataclass(frozen=True, slots=True)
class SumScalarField:
    """Add independent scalar samplers in the same query coordinate system."""

    samplers: tuple[ScalarSampler, ...]
    gradient_samplers: tuple[ScalarGradientSampler, ...] | None = None

    def sample(self, positions: np.ndarray) -> np.ndarray:
        query_points = np.asarray(positions, dtype=np.float64)
        total = np.zeros(len(query_points), dtype=np.float64)
        for sampler in self.samplers:
            total += sampler(query_points)
        total.setflags(write=False)
        return total

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Add values and their gradients in the same input-coordinate frame."""
        query_points = np.asarray(positions, dtype=np.float64)
        total = np.zeros(len(query_points), dtype=np.float64)
        gradients = np.zeros((len(query_points), 3), dtype=np.float64)
        for sampler in self.gradient_samplers:
            sample = sampler(query_points)
            total += sample.values
            gradients += sample.gradients
        return ScalarSample(total, gradients)


@dataclass(frozen=True, slots=True)
class WarpedVectorField:
    """Transport source tangent vectors through an inverse coordinate map.

    The supplied transform maps query coordinates to source coordinates.
    Only transported values are requested here; their spatial Jacobians would
    also require second derivatives of the coordinate transform.
    """

    transform_with_jacobian: VectorJacobianSampler
    sample_source: VectorSampler

    def sample(self, positions: np.ndarray) -> np.ndarray:
        transformed = self.transform_with_jacobian(
            np.asarray(positions, dtype=np.float64)
        )
        return pullback_vectors(
            self.sample_source(transformed.values), transformed.jacobians
        )


@dataclass(frozen=True, slots=True)
class WarpedNormalField:
    """Pull back source normals with J transpose and restore unit length."""

    transform_with_jacobian: VectorJacobianSampler
    sample_source: VectorSampler

    def sample(self, positions: np.ndarray) -> np.ndarray:
        transformed = self.transform_with_jacobian(
            np.asarray(positions, dtype=np.float64)
        )
        return pullback_normals(
            self.sample_source(transformed.values), transformed.jacobians
        )


@dataclass(frozen=True, slots=True)
class PushforwardVectorField:
    """Push vector components forward while keeping source query coordinates."""

    transform_with_jacobian: VectorJacobianSampler
    sample_source: VectorSampler
    transform_with_hessian: VectorHessianSampler
    sample_source_with_jacobian: VectorJacobianSampler

    def sample(self, positions: np.ndarray) -> np.ndarray:
        query_points = np.asarray(positions, dtype=np.float64)
        transformed = self.transform_with_jacobian(query_points)
        return pushforward_vectors(
            self.sample_source(query_points), transformed.jacobians
        )

    def sample_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        query_points = np.asarray(positions, dtype=np.float64)
        transformed = self.transform_with_hessian(query_points)
        source = self.sample_source_with_jacobian(query_points)
        jacobians = pushforward_vector_jacobians(
            source.values,
            source.jacobians,
            transformed.jacobians,
            transformed.hessians,
        )
        return VectorSample(
            pushforward_vectors(source.values, transformed.jacobians), jacobians
        )


@dataclass(frozen=True, slots=True)
class ReparameterizedVectorField:
    """Compose vector coordinates without transporting vector components."""

    transform: CoordinateTransform
    sample_source: VectorSampler
    transform_with_jacobian: VectorJacobianSampler
    sample_source_with_jacobian: VectorJacobianSampler

    def sample(self, positions: np.ndarray) -> np.ndarray:
        return self.sample_source(
            self.transform(np.asarray(positions, dtype=np.float64))
        )

    def sample_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        transformed = self.transform_with_jacobian(
            np.asarray(positions, dtype=np.float64)
        )
        source = self.sample_source_with_jacobian(transformed.values)
        jacobians = np.einsum(
            "...ab,...bc->...ac", source.jacobians, transformed.jacobians
        )
        return VectorSample(source.values, jacobians)
