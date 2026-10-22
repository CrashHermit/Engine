"""Sparse pair interactions derived from overlapping regional memberships."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceField,
    RegionInfluenceSample,
)


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
        weights = sample.weights
        distances_squared = sample.voronoi.distances_squared
        query_parts: list[np.ndarray] = []
        pair_index_parts: list[np.ndarray] = []
        influence_parts: list[np.ndarray] = []
        distance_parts: list[np.ndarray] = []

        for pair_index, ((region_a, region_b), inverse_separation) in enumerate(
            zip(
                self.regions.region_pairs,
                self.regions.inverse_pair_separations,
                strict=True,
            )
        ):
            pair_influence = 4.0 * weights[:, region_a] * weights[:, region_b]
            active = np.flatnonzero(pair_influence > 0.0)
            if len(active) == 0:
                continue
            plane_distance = (
                distances_squared[:, region_a] - distances_squared[:, region_b]
            ) * (0.5 * inverse_separation)
            query_parts.append(active)
            pair_index_parts.append(np.full(len(active), pair_index, dtype=np.int64))
            influence_parts.append(pair_influence[active])
            distance_parts.append(plane_distance[active])

        if not query_parts:
            query_indices = np.empty(0, dtype=np.int64)
            region_pairs = np.empty((0, 2), dtype=np.int64)
            influence = np.empty(0, dtype=np.float64)
            plane_distance = np.empty(0, dtype=np.float64)
            normals = np.empty((0, 3), dtype=np.float64)
        else:
            query_indices = np.concatenate(query_parts)
            pair_indices = np.concatenate(pair_index_parts)
            influence = np.concatenate(influence_parts)
            plane_distance = np.concatenate(distance_parts)
            order = np.lexsort((pair_indices, query_indices))
            query_indices = query_indices[order]
            pair_indices = pair_indices[order]
            influence = influence[order]
            plane_distance = plane_distance[order]
            region_pairs = self.regions.region_pairs[pair_indices]
            normals = self.regions.pair_normals[pair_indices]

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
