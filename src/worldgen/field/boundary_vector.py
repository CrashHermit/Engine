"""Compose algebraic region overlap with selected region vector fields."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import VectorSample
from src.worldgen.field.region_overlap import RegionOverlapField, RegionOverlapSample


type RegionVectorSampler = Callable[[np.ndarray, np.ndarray], np.ndarray]
type RegionVectorJacobianSampler = Callable[[np.ndarray, np.ndarray], VectorSample]


@dataclass(frozen=True, slots=True)
class BoundaryVectorSample:
    """Sparse per-query region interactions and their paired vectors."""

    query_indices: np.ndarray
    region_pairs: np.ndarray
    influence: np.ndarray
    vectors: np.ndarray
    plane_distance: np.ndarray
    normals: np.ndarray


@dataclass(frozen=True, slots=True)
class BoundaryVectorJacobianSample:
    """Paired vectors and their source Jacobians (pair, side, output, input)."""

    sample: BoundaryVectorSample
    jacobians: np.ndarray

    def __post_init__(self) -> None:
        self.jacobians.setflags(write=False)


def _unique_region_requests(
    overlap: RegionOverlapSample,
) -> tuple[np.ndarray, np.ndarray]:
    requests = np.empty((2 * len(overlap.query_indices), 2), dtype=np.int64)
    requests[:, 0] = np.repeat(overlap.query_indices, 2)
    requests[:, 1] = overlap.region_pairs.reshape(-1)
    return np.unique(requests, axis=0, return_inverse=True)


def _vector_sample(
    overlap: RegionOverlapSample, vectors: np.ndarray
) -> BoundaryVectorSample:
    for values in (
        overlap.query_indices,
        overlap.region_pairs,
        overlap.influence,
        vectors,
        overlap.plane_distance,
        overlap.normals,
    ):
        values.setflags(write=False)
    return BoundaryVectorSample(
        query_indices=overlap.query_indices,
        region_pairs=overlap.region_pairs,
        influence=overlap.influence,
        vectors=vectors,
        plane_distance=overlap.plane_distance,
        normals=overlap.normals,
    )


@dataclass(frozen=True, slots=True)
class BoundaryVectorField:
    """Evaluate region vectors selected by continuous pair overlap."""

    overlap: RegionOverlapField
    sample_regions: RegionVectorSampler
    sample_region_jacobians: RegionVectorJacobianSampler | None = None

    def sample(self, positions: np.ndarray) -> BoundaryVectorSample:
        """Return every active pair at arbitrary Cartesian positions."""
        points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_overlap(points, self.overlap.sample(points))

    def sample_owner_vectors(self, positions: np.ndarray) -> np.ndarray:
        """Select each point's source vector without requiring caller region IDs."""
        points = np.asarray(positions, dtype=np.float64)
        owners = self.overlap.regions.partition.sample(points).owner_seed_id
        values = self.sample_regions(points, owners)
        values.setflags(write=False)
        return values

    def sample_owner_vectors_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        """Return ownership-selected vectors and their piecewise source Jacobians."""
        points = np.asarray(positions, dtype=np.float64)
        owners = self.overlap.regions.partition.sample(points).owner_seed_id
        return self.sample_region_jacobians(points, owners)

    def sample_from_overlap(
        self, positions: np.ndarray, overlap: RegionOverlapSample
    ) -> BoundaryVectorSample:
        """Reuse pair overlap and evaluate each requested query/region only once."""
        points = np.asarray(positions, dtype=np.float64)
        if len(overlap.query_indices) == 0:
            vectors = np.empty((0, 2, 3), dtype=np.float64)
        else:
            requests, inverse = _unique_region_requests(overlap)
            vectors = self.sample_regions(points[requests[:, 0]], requests[:, 1])
            vectors = vectors[inverse].reshape((-1, 2, 3))
        return _vector_sample(overlap, vectors)

    def sample_with_jacobian(
        self, positions: np.ndarray
    ) -> BoundaryVectorJacobianSample:
        """Return paired vectors and analytic Jacobians without caller region IDs."""
        points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_overlap_with_jacobian(
            points, self.overlap.sample(points)
        )

    def sample_from_overlap_with_jacobian(
        self, positions: np.ndarray, overlap: RegionOverlapSample
    ) -> BoundaryVectorJacobianSample:
        """Reuse one analytic vector evaluation for each unique query/region."""
        points = np.asarray(positions, dtype=np.float64)
        if len(overlap.query_indices) == 0:
            vectors = np.empty((0, 2, 3), dtype=np.float64)
            jacobians = np.empty((0, 2, 3, 3), dtype=np.float64)
        else:
            requests, inverse = _unique_region_requests(overlap)
            sample = self.sample_region_jacobians(
                points[requests[:, 0]], requests[:, 1]
            )
            vectors = sample.values[inverse].reshape((-1, 2, 3))
            jacobians = sample.jacobians[inverse].reshape((-1, 2, 3, 3))
        return BoundaryVectorJacobianSample(_vector_sample(overlap, vectors), jacobians)
