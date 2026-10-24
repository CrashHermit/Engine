"""Per-pair Cartesian motion components at overlapping region influences."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from scipy.special import expit

from src.worldgen.field.boundary_vector import (
    BoundaryVectorJacobianSample,
    BoundaryVectorSample,
)
from src.worldgen.field.region_influence import RegionInfluenceSample
from src.worldgen.field.region_overlap import RegionOverlapField, RegionOverlapSample
from src.worldgen.geometry.vector import relative_motion_components
from src.worldgen.utilities.smooth import smooth_maximum, smooth_minimum


class BoundaryVectorSource(Protocol):
    overlap: RegionOverlapField

    def sample_from_overlap(
        self, positions: np.ndarray, overlap: RegionOverlapSample
    ) -> BoundaryVectorSample: ...

    def sample_from_overlap_with_jacobian(
        self, positions: np.ndarray, overlap: RegionOverlapSample
    ) -> BoundaryVectorJacobianSample: ...


@dataclass(frozen=True, slots=True)
class BoundaryMotionConfig:
    """Positive transition scales for smooth opening splits and tangent magnitudes."""

    opening_smoothing_width: float = 0.01
    shear_smoothing: float = 0.01


@dataclass(frozen=True, slots=True)
class BoundaryMotionSample:
    """Sparse region-pair metadata and unweighted smooth motion components."""

    query_indices: np.ndarray
    region_pairs: np.ndarray
    plane_distance: np.ndarray
    influence: np.ndarray
    normals: np.ndarray
    opening: np.ndarray
    convergence: np.ndarray
    divergence: np.ndarray
    shear: np.ndarray


@dataclass(frozen=True, slots=True)
class BoundaryMotionGradientSample:
    sample: BoundaryMotionSample
    plane_distance_gradients: np.ndarray
    influence_gradients: np.ndarray
    opening_gradients: np.ndarray
    convergence_gradients: np.ndarray
    divergence_gradients: np.ndarray
    shear_gradients: np.ndarray
    normal_jacobians: np.ndarray

    def __post_init__(self) -> None:
        for gradient in (
            self.plane_distance_gradients,
            self.influence_gradients,
            self.opening_gradients,
            self.convergence_gradients,
            self.divergence_gradients,
            self.shear_gradients,
            self.normal_jacobians,
        ):
            gradient.setflags(write=False)


@dataclass(frozen=True, slots=True)
class BoundaryMotionField:
    """Resolve region-pair motion against source or transported boundary vectors."""

    vectors: BoundaryVectorSource
    config: BoundaryMotionConfig = BoundaryMotionConfig()

    def sample(self, positions: np.ndarray) -> BoundaryMotionSample:
        query_points = np.asarray(positions, dtype=np.float64)
        overlap_sample = self.vectors.overlap.sample(query_points)
        return self.sample_from_overlap(query_points, overlap_sample)

    def sample_from_overlap(
        self, positions: np.ndarray, overlap: RegionOverlapSample
    ) -> BoundaryMotionSample:
        return self.sample_from_vectors(
            self.vectors.sample_from_overlap(positions, overlap)
        )

    def sample_from_vectors(
        self, vector_sample: BoundaryVectorSample
    ) -> BoundaryMotionSample:
        opening, shear = relative_motion_components(
            vector_sample.vectors[:, 0, :],
            vector_sample.vectors[:, 1, :],
            vector_sample.normals,
            shear_smoothing=self.config.shear_smoothing,
        )
        convergence = -smooth_minimum(
            opening, 0.0, width=self.config.opening_smoothing_width
        )
        divergence = smooth_maximum(
            opening, 0.0, width=self.config.opening_smoothing_width
        )
        for values in (opening, convergence, divergence, shear):
            values.setflags(write=False)
        return BoundaryMotionSample(
            query_indices=vector_sample.query_indices,
            region_pairs=vector_sample.region_pairs,
            plane_distance=vector_sample.plane_distance,
            influence=vector_sample.influence,
            normals=vector_sample.normals,
            opening=opening,
            convergence=convergence,
            divergence=divergence,
            shear=shear,
        )

    def sample_with_gradient(
        self, positions: np.ndarray
    ) -> BoundaryMotionGradientSample:
        points = np.asarray(positions, dtype=np.float64)
        regions, gradients = self.vectors.overlap.regions.sample_with_gradient(points)
        return self.sample_from_regions_with_gradient(points, regions, gradients)

    def sample_from_regions_with_gradient(
        self,
        positions: np.ndarray,
        memberships: RegionInfluenceSample,
        membership_gradients: np.ndarray,
        *,
        overlap_sample: RegionOverlapSample | None = None,
        vector_sample: BoundaryVectorJacobianSample | None = None,
    ) -> BoundaryMotionGradientSample:
        """Reuse regional and transported vector differentials for motion channels."""
        points = np.asarray(positions, dtype=np.float64)
        overlap = (
            self.vectors.overlap.sample_from_regions(memberships)
            if overlap_sample is None
            else overlap_sample
        )
        vectors = (
            self.vectors.sample_from_overlap_with_jacobian(points, overlap)
            if vector_sample is None
            else vector_sample
        )
        sample = self.sample_from_vectors(vectors.sample)
        plane_gradients = overlap.normals
        rows = overlap.query_indices
        a, b = overlap.region_pairs.T
        influence_gradients = 4.0 * (
            membership_gradients[rows, a] * memberships.weights[rows, b, None]
            + memberships.weights[rows, a, None] * membership_gradients[rows, b]
        )
        relative = vectors.sample.vectors[:, 1] - vectors.sample.vectors[:, 0]
        relative_jacobian = vectors.jacobians[:, 1] - vectors.jacobians[:, 0]
        opening_gradients = np.einsum(
            "nij,ni->nj", relative_jacobian, sample.normals
        ) + np.einsum("ni,nij->nj", relative, vectors.normal_jacobians)
        scaled_opening = sample.opening / self.config.opening_smoothing_width
        convergence_gradients = -expit(-scaled_opening)[:, None] * opening_gradients
        divergence_gradients = expit(scaled_opening)[:, None] * opening_gradients
        sliding = relative - sample.opening[:, None] * sample.normals
        sliding_gradient = (
            relative_jacobian
            - np.einsum("ni,nj->nij", sample.normals, opening_gradients)
            - sample.opening[:, None, None] * vectors.normal_jacobians
        )
        squared = np.einsum("ni,ni->n", sliding, sliding)
        shear_gradients = (
            np.einsum("ni,nij->nj", sliding, sliding_gradient)
            / np.sqrt(squared + self.config.shear_smoothing**2)[:, None]
        )
        return BoundaryMotionGradientSample(
            sample=sample,
            plane_distance_gradients=plane_gradients,
            influence_gradients=influence_gradients,
            opening_gradients=opening_gradients,
            convergence_gradients=convergence_gradients,
            divergence_gradients=divergence_gradients,
            shear_gradients=shear_gradients,
            normal_jacobians=vectors.normal_jacobians,
        )
