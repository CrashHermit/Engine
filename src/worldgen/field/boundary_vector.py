"""Compose boundary influence with selected region vector fields."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.field.boundary import VoronoiBoundaryField


type RegionVectorSampler = Callable[[np.ndarray, np.ndarray], np.ndarray]


@dataclass(frozen=True, slots=True)
class BoundaryVectorSample:
    """Sparse per-query boundary interactions and their paired region vectors."""

    query_indices: np.ndarray
    region_pairs: np.ndarray
    influence: np.ndarray
    vectors: np.ndarray


@dataclass(frozen=True, slots=True)
class BoundaryVectorField:
    """Evaluate only the region vectors selected by nearby boundary influence."""

    boundary: VoronoiBoundaryField
    sample_regions: RegionVectorSampler

    def sample(self, positions: np.ndarray) -> BoundaryVectorSample:
        """Return active boundary-pair records at arbitrary Cartesian positions."""
        query_points = np.asarray(positions, dtype=np.float64)
        boundary_sample = self.boundary.sample(query_points)
        query_indices, face_indices = np.nonzero(boundary_sample.influence > 0.0)
        region_pairs = boundary_sample.region_pairs[face_indices]
        influence = boundary_sample.influence[query_indices, face_indices]

        if len(query_indices) == 0:
            query_indices = np.empty(0, dtype=np.int64)
            region_pairs = np.empty((0, 2), dtype=np.int64)
            influence = np.empty(0, dtype=np.float64)
            vectors = np.empty((0, 2, 3), dtype=np.float64)
        else:
            query_indices = np.asarray(query_indices, dtype=np.int64)
            requests = np.empty((2 * len(query_indices), 2), dtype=np.int64)
            requests[:, 0] = np.repeat(query_indices, 2)
            requests[:, 1] = region_pairs.reshape(-1)
            unique_requests, inverse = np.unique(requests, axis=0, return_inverse=True)
            region_vectors = self.sample_regions(
                query_points[unique_requests[:, 0]], unique_requests[:, 1]
            )
            vectors = region_vectors[inverse].reshape((-1, 2, 3))

        for array in (query_indices, region_pairs, influence, vectors):
            array.setflags(write=False)
        return BoundaryVectorSample(
            query_indices=query_indices,
            region_pairs=region_pairs,
            influence=influence,
            vectors=vectors,
        )
