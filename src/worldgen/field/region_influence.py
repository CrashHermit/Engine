"""Smooth normalized membership fields over a Cartesian Voronoi partition."""

from dataclasses import dataclass, field

import numpy as np
from numba import njit, prange
from numba.extending import register_jitable

from src.worldgen.field.voronoi import VoronoiField3D, VoronoiSample
from src.worldgen.utilities.curves import clamp_unit, smoothstep_scalar


@register_jitable(inline="always")
def _membership_products(
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    inverse_pair_separations: np.ndarray,
    half_width: float,
) -> np.ndarray:
    """Evaluate unnormalized pairwise membership products."""
    query_count, seed_count = distances_squared.shape
    memberships = np.empty((query_count, seed_count), dtype=np.float64)
    for query_index in prange(query_count):
        for region_index in range(seed_count):
            memberships[query_index, region_index] = 1.0
        for pair_index in range(len(region_pairs)):
            region_a = region_pairs[pair_index, 0]
            region_b = region_pairs[pair_index, 1]
            plane_distance = (
                distances_squared[query_index, region_a]
                - distances_squared[query_index, region_b]
            ) * (0.5 * inverse_pair_separations[pair_index])
            scaled_distance = plane_distance / (2.0 * half_width)
            factor_a = smoothstep_scalar(0.5 - scaled_distance)
            factor_b = smoothstep_scalar(0.5 + scaled_distance)
            memberships[query_index, region_a] *= factor_a
            memberships[query_index, region_b] *= factor_b
    return memberships


@register_jitable(inline="always")
def _membership_products_with_gradient(
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    pair_normals: np.ndarray,
    inverse_pair_separations: np.ndarray,
    half_width: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate regional membership products and their Cartesian gradients."""
    query_count, seed_count = distances_squared.shape
    memberships = np.empty((query_count, seed_count), dtype=np.float64)
    membership_gradients = np.empty((query_count, seed_count, 3), dtype=np.float64)
    for query_index in prange(query_count):
        for region_index in range(seed_count):
            memberships[query_index, region_index] = 1.0
            for axis in range(3):
                membership_gradients[query_index, region_index, axis] = 0.0
        for pair_index in range(len(region_pairs)):
            region_a = region_pairs[pair_index, 0]
            region_b = region_pairs[pair_index, 1]
            plane_distance = (
                distances_squared[query_index, region_a]
                - distances_squared[query_index, region_b]
            ) * (0.5 * inverse_pair_separations[pair_index])
            scaled_distance = plane_distance / (2.0 * half_width)
            x_a = clamp_unit(0.5 - scaled_distance)
            x_b = clamp_unit(0.5 + scaled_distance)
            factor_a = smoothstep_scalar(x_a)
            factor_b = smoothstep_scalar(x_b)
            derivative_a = -6.0 * x_a * (1.0 - x_a) / (2.0 * half_width)
            derivative_b = 6.0 * x_b * (1.0 - x_b) / (2.0 * half_width)
            for axis in range(3):
                normal_component = pair_normals[pair_index, axis]
                membership_gradients[query_index, region_a, axis] = (
                    membership_gradients[query_index, region_a, axis] * factor_a
                    + memberships[query_index, region_a]
                    * derivative_a
                    * normal_component
                )
                membership_gradients[query_index, region_b, axis] = (
                    membership_gradients[query_index, region_b, axis] * factor_b
                    + memberships[query_index, region_b]
                    * derivative_b
                    * normal_component
                )
            memberships[query_index, region_a] *= factor_a
            memberships[query_index, region_b] *= factor_b
    return memberships, membership_gradients


# Separate entry points give the serial and parallel variants distinct cache keys.
@njit(cache=True)
def _membership_products_serial(
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    inverse_separations: np.ndarray,
    width: float,
) -> np.ndarray:
    return _membership_products(
        distances_squared, region_pairs, inverse_separations, width
    )


@njit(cache=True, parallel=True)
def _membership_products_parallel(
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    inverse_separations: np.ndarray,
    width: float,
) -> np.ndarray:
    return _membership_products(
        distances_squared, region_pairs, inverse_separations, width
    )


@njit(cache=True)
def _membership_gradients_serial(
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    normals: np.ndarray,
    inverse_separations: np.ndarray,
    width: float,
) -> tuple[np.ndarray, np.ndarray]:
    return _membership_products_with_gradient(
        distances_squared, region_pairs, normals, inverse_separations, width
    )


@njit(cache=True, parallel=True)
def _membership_gradients_parallel(
    distances_squared: np.ndarray,
    region_pairs: np.ndarray,
    normals: np.ndarray,
    inverse_separations: np.ndarray,
    width: float,
) -> tuple[np.ndarray, np.ndarray]:
    return _membership_products_with_gradient(
        distances_squared, region_pairs, normals, inverse_separations, width
    )


# Small queries cost less than a thread launch in the measured 8–40 seed cases.
_PARALLEL_PAIR_WORK = 32_768


@dataclass(frozen=True, slots=True)
class RegionInfluenceConfig:
    """Source-space half-width of each pairwise transition."""

    transition_half_width: float = 0.12


@dataclass(frozen=True, slots=True)
class RegionInfluenceSample:
    """Categorical partition query and normalized regional memberships."""

    voronoi: VoronoiSample
    weights: np.ndarray


@dataclass(frozen=True, slots=True)
class RegionInfluenceField:
    """Compose smooth regional memberships from reusable seed distances."""

    partition: VoronoiField3D
    config: RegionInfluenceConfig = RegionInfluenceConfig()
    region_pairs: np.ndarray = field(init=False, repr=False)
    pair_normals: np.ndarray = field(init=False, repr=False)
    inverse_pair_separations: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        seed_count = len(self.partition.seeds)
        pair_rows = np.stack(np.triu_indices(seed_count, k=1), axis=1).astype(
            np.int64, copy=False
        )
        separations = (
            self.partition.seeds[pair_rows[:, 1]]
            - self.partition.seeds[pair_rows[:, 0]]
        )
        lengths = np.sqrt(np.sum(separations * separations, axis=1))
        pair_normals = separations / lengths[:, None]
        inverse_pair_separations = 1.0 / lengths

        for values in (pair_rows, pair_normals, inverse_pair_separations):
            values.setflags(write=False)
        object.__setattr__(self, "region_pairs", pair_rows)
        object.__setattr__(self, "pair_normals", pair_normals)
        object.__setattr__(self, "inverse_pair_separations", inverse_pair_separations)

    def sample(self, positions: np.ndarray) -> RegionInfluenceSample:
        """Sample regional memberships at arbitrary Cartesian positions."""
        return self.sample_from_voronoi(self.partition.sample(positions))

    def sample_with_gradient(
        self, positions: np.ndarray
    ) -> tuple[RegionInfluenceSample, np.ndarray]:
        """Sample normalized memberships and analytic Cartesian gradients."""
        return self.sample_from_voronoi_with_gradient(self.partition.sample(positions))

    def sample_from_voronoi_with_gradient(
        self, sample: VoronoiSample
    ) -> tuple[RegionInfluenceSample, np.ndarray]:
        """Derive membership gradients from shared squared seed distances."""
        query_count = len(sample.distances_squared)
        kernel = _membership_gradients_serial
        if (
            query_count >= 64
            and query_count * len(self.region_pairs) >= _PARALLEL_PAIR_WORK
        ):
            kernel = _membership_gradients_parallel
        memberships, membership_gradients = kernel(
            sample.distances_squared,
            self.region_pairs,
            self.pair_normals,
            self.inverse_pair_separations,
            self.config.transition_half_width,
        )
        totals = np.sum(memberships, axis=1, keepdims=True)
        total_gradients = np.sum(membership_gradients, axis=1, keepdims=True)
        weights = memberships / totals
        gradients = (
            membership_gradients - weights[:, :, None] * total_gradients
        ) / totals[:, :, None]
        weights.setflags(write=False)
        gradients.setflags(write=False)
        return RegionInfluenceSample(voronoi=sample, weights=weights), gradients

    def sample_from_voronoi(self, sample: VoronoiSample) -> RegionInfluenceSample:
        """Derive memberships from an already evaluated seed-distance query."""
        query_count = len(sample.distances_squared)
        kernel = _membership_products_serial
        if (
            query_count >= 64
            and query_count * len(self.region_pairs) >= _PARALLEL_PAIR_WORK
        ):
            kernel = _membership_products_parallel
        memberships = kernel(
            sample.distances_squared,
            self.region_pairs,
            self.inverse_pair_separations,
            self.config.transition_half_width,
        )
        weights = memberships / np.sum(memberships, axis=1, keepdims=True)
        weights.setflags(write=False)
        return RegionInfluenceSample(voronoi=sample, weights=weights)
