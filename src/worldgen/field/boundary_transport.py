"""Transport paired boundary vectors and normals through a coordinate map."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.boundary_vector import (
    BoundaryVectorField,
    BoundaryVectorJacobianSample,
    BoundaryVectorSample,
)
from src.worldgen.field.differential import (
    VectorHessianSample,
    VectorHessianSampler,
    VectorJacobianSampler,
    VectorSample,
)
from src.worldgen.field.region_overlap import RegionOverlapField, RegionOverlapSample
from src.worldgen.geometry.differential import (
    pushforward_normal_jacobians,
    pushforward_normals,
    pushforward_vector_jacobians,
)


@dataclass(frozen=True, slots=True)
class TransportedBoundaryVectorField:
    """Evaluate source pair fields, transporting vectors and normals to world frame."""

    source: BoundaryVectorField
    source_to_world_with_jacobian: VectorJacobianSampler
    source_to_world_with_hessian: VectorHessianSampler

    @property
    def overlap(self) -> RegionOverlapField:
        return self.source.overlap

    def sample(self, positions: np.ndarray) -> BoundaryVectorSample:
        points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_overlap(points, self.overlap.sample(points))

    def sample_from_overlap(
        self,
        positions: np.ndarray,
        overlap: RegionOverlapSample,
        *,
        transformation: VectorSample | None = None,
    ) -> BoundaryVectorSample:
        points = np.asarray(positions, dtype=np.float64)
        mapping = (
            self.source_to_world_with_jacobian(points)
            if transformation is None
            else transformation
        )
        source_sample = self.source.sample_from_overlap(points, overlap)
        pair_jacobians = mapping.jacobians[overlap.query_indices]
        vectors = np.einsum("nij,nkj->nki", pair_jacobians, source_sample.vectors)
        normals = pushforward_normals(source_sample.normals, pair_jacobians)
        vectors.setflags(write=False)
        normals.setflags(write=False)
        return BoundaryVectorSample(
            source_sample.query_indices,
            source_sample.region_pairs,
            source_sample.influence,
            vectors,
            source_sample.plane_distance,
            normals,
        )

    def sample_with_jacobian(
        self, positions: np.ndarray
    ) -> BoundaryVectorJacobianSample:
        points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_overlap_with_jacobian(
            points, self.overlap.sample(points)
        )

    def sample_from_overlap_with_jacobian(
        self,
        positions: np.ndarray,
        overlap: RegionOverlapSample,
        *,
        transformation: VectorHessianSample | None = None,
    ) -> BoundaryVectorJacobianSample:
        points = np.asarray(positions, dtype=np.float64)
        mapping = (
            self.source_to_world_with_hessian(points)
            if transformation is None
            else transformation
        )
        source_sample = self.source.sample_from_overlap_with_jacobian(points, overlap)
        pair_jacobians = mapping.jacobians[overlap.query_indices]
        pair_hessians = mapping.hessians[overlap.query_indices]
        vectors = np.einsum(
            "nij,nkj->nki", pair_jacobians, source_sample.sample.vectors
        )
        normals = pushforward_normals(source_sample.sample.normals, pair_jacobians)
        vector_jacobians = pushforward_vector_jacobians(
            source_sample.sample.vectors,
            source_sample.jacobians,
            pair_jacobians,
            pair_hessians,
        )
        normal_jacobians = pushforward_normal_jacobians(
            source_sample.sample.normals,
            source_sample.normal_jacobians,
            pair_jacobians,
            pair_hessians,
        )
        sample = BoundaryVectorSample(
            source_sample.sample.query_indices,
            source_sample.sample.region_pairs,
            source_sample.sample.influence,
            vectors,
            source_sample.sample.plane_distance,
            normals,
        )
        for values in (vectors, normals, vector_jacobians, normal_jacobians):
            values.setflags(write=False)
        return BoundaryVectorJacobianSample(sample, vector_jacobians, normal_jacobians)

    def sample_owner_vectors(self, positions: np.ndarray) -> np.ndarray:
        points = np.asarray(positions, dtype=np.float64)
        mapping = self.source_to_world_with_jacobian(points)
        values = np.einsum(
            "nij,nj->ni", mapping.jacobians, self.source.sample_owner_vectors(points)
        )
        values.setflags(write=False)
        return values

    def sample_owner_vectors_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        points = np.asarray(positions, dtype=np.float64)
        mapping = self.source_to_world_with_hessian(points)
        source = self.source.sample_owner_vectors_with_jacobian(points)
        values = np.einsum("nij,nj->ni", mapping.jacobians, source.values)
        jacobians = pushforward_vector_jacobians(
            source.values, source.jacobians, mapping.jacobians, mapping.hessians
        )
        values.setflags(write=False)
        return VectorSample(values, jacobians)
