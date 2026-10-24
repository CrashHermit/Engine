"""Sparse pair interactions derived from overlapping regional memberships."""

from dataclasses import dataclass

import numpy as np
from numba import njit, prange
from numba.extending import register_jitable

from src.worldgen.field.region_influence import (
    RegionInfluenceField,
    RegionInfluenceSample,
)


@register_jitable(inline="always")
def _overlap_arrays(
    weights: np.ndarray,
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    inverse_pair_separations: np.ndarray,
    pair_normals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract active ordered region pairs into exact-size output arrays."""
    query_count = weights.shape[0]
    pair_count = len(region_pairs)
    offsets = np.empty(query_count + 1, dtype=np.int64)
    offsets[0] = 0
    for query_index in prange(query_count):
        count = 0
        for pair_index in range(pair_count):
            region_a = region_pairs[pair_index, 0]
            region_b = region_pairs[pair_index, 1]
            if (
                4.0 * weights[query_index, region_a] * weights[query_index, region_b]
                > 0.0
            ):
                count += 1
        offsets[query_index + 1] = count

    for query_index in range(query_count):
        offsets[query_index + 1] += offsets[query_index]
    record_count = offsets[query_count]

    query_indices = np.empty(record_count, dtype=np.int64)
    active_pairs = np.empty((record_count, 2), dtype=np.int64)
    influence = np.empty(record_count, dtype=np.float64)
    plane_distance = np.empty(record_count, dtype=np.float64)
    normals = np.empty((record_count, 3), dtype=np.float64)
    for query_index in prange(query_count):
        record_index = offsets[query_index]
        for pair_index in range(pair_count):
            region_a = region_pairs[pair_index, 0]
            region_b = region_pairs[pair_index, 1]
            pair_influence = (
                4.0 * weights[query_index, region_a] * weights[query_index, region_b]
            )
            if pair_influence > 0.0:
                query_indices[record_index] = query_index
                active_pairs[record_index, 0] = region_a
                active_pairs[record_index, 1] = region_b
                influence[record_index] = pair_influence
                plane_distance[record_index] = (
                    distances_squared[query_index, region_a]
                    - distances_squared[query_index, region_b]
                ) * (0.5 * inverse_pair_separations[pair_index])
                for axis in range(3):
                    normals[record_index, axis] = pair_normals[pair_index, axis]
                record_index += 1
    return query_indices, active_pairs, influence, plane_distance, normals


@njit(cache=True)
def _overlap_arrays_serial(
    weights: np.ndarray,
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    inverse_separations: np.ndarray,
    normals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return _overlap_arrays(
        weights, distances_squared, region_pairs, inverse_separations, normals
    )


@njit(cache=True, parallel=True)
def _overlap_arrays_parallel(
    weights: np.ndarray,
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    inverse_separations: np.ndarray,
    normals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return _overlap_arrays(
        weights, distances_squared, region_pairs, inverse_separations, normals
    )


# Counting and filling each launch workers, so keep small queries sequential.
_PARALLEL_PAIR_WORK = 32_768


@dataclass(frozen=True, slots=True)
class RegionOverlapSample:
    """Positive pair overlap records at their original query positions."""

    query_indices: np.ndarray
    region_pairs: np.ndarray
    influence: np.ndarray
    plane_distance: np.ndarray
    normals: np.ndarray


@dataclass(frozen=True, slots=True)
class RegionOverlapField:
    """Compose every positive pair product without constructing face geometry."""

    regions: RegionInfluenceField

    def sample(self, positions: np.ndarray) -> RegionOverlapSample:
        """Sample all overlapping region pairs at Cartesian positions."""
        return self.sample_from_regions(self.regions.sample(positions))

    def sample_from_regions(self, sample: RegionInfluenceSample) -> RegionOverlapSample:
        """Derive sparse pair contributions from an existing membership sample."""
        query_count = len(sample.weights)
        kernel = _overlap_arrays_serial
        if (
            query_count >= 64
            and query_count * len(self.regions.region_pairs) >= _PARALLEL_PAIR_WORK
        ):
            kernel = _overlap_arrays_parallel
        (
            query_indices,
            region_pairs,
            influence,
            plane_distance,
            normals,
        ) = kernel(
            sample.weights,
            sample.voronoi.distances_squared,
            self.regions.region_pairs,
            self.regions.inverse_pair_separations,
            self.regions.pair_normals,
        )

        for values in (
            query_indices,
            region_pairs,
            influence,
            plane_distance,
            normals,
        ):
            values.setflags(write=False)
        return RegionOverlapSample(
            query_indices=query_indices,
            region_pairs=region_pairs,
            influence=influence,
            plane_distance=plane_distance,
            normals=normals,
        )
