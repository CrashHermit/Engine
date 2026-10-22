"""Smooth normalized membership fields over a Cartesian Voronoi partition."""

from dataclasses import dataclass, field

import numpy as np

from src.worldgen.field.voronoi import VoronoiField3D, VoronoiSample
from src.worldgen.utilities.curves import smoothstep


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
        query_count, seed_count = sample.distances_squared.shape
        memberships = np.ones((query_count, seed_count), dtype=np.float64)
        membership_gradients = np.zeros((query_count, seed_count, 3), dtype=np.float64)
        half_width = self.config.transition_half_width
        for (region_a, region_b), normal, inverse_separation in zip(
            self.region_pairs,
            self.pair_normals,
            self.inverse_pair_separations,
            strict=True,
        ):
            plane_distance = (
                sample.distances_squared[:, region_a]
                - sample.distances_squared[:, region_b]
            ) * (0.5 * inverse_separation)
            scaled = plane_distance / (2.0 * half_width)
            x_a = np.clip(0.5 - scaled, 0.0, 1.0)
            x_b = np.clip(0.5 + scaled, 0.0, 1.0)
            factor_a = smoothstep(x_a)
            factor_b = smoothstep(x_b)
            derivative_a = -6.0 * x_a * (1.0 - x_a) / (2.0 * half_width)
            derivative_b = 6.0 * x_b * (1.0 - x_b) / (2.0 * half_width)
            membership_gradients[:, region_a] = (
                membership_gradients[:, region_a] * factor_a[:, None]
                + memberships[:, region_a, None] * derivative_a[:, None] * normal
            )
            membership_gradients[:, region_b] = (
                membership_gradients[:, region_b] * factor_b[:, None]
                + memberships[:, region_b, None] * derivative_b[:, None] * normal
            )
            memberships[:, region_a] *= factor_a
            memberships[:, region_b] *= factor_b
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
        query_count, seed_count = sample.distances_squared.shape
        memberships = np.ones((query_count, seed_count), dtype=np.float64)
        half_width = self.config.transition_half_width

        for (region_a, region_b), inverse_separation in zip(
            self.region_pairs, self.inverse_pair_separations, strict=True
        ):
            plane_distance = (
                sample.distances_squared[:, region_a]
                - sample.distances_squared[:, region_b]
            ) * (0.5 * inverse_separation)
            scaled_distance = plane_distance / (2.0 * half_width)
            membership_a = smoothstep(0.5 - scaled_distance)
            membership_b = smoothstep(0.5 + scaled_distance)
            memberships[:, region_a] *= membership_a
            memberships[:, region_b] *= membership_b

        weights = memberships / np.sum(memberships, axis=1, keepdims=True)
        weights.setflags(write=False)
        return RegionInfluenceSample(voronoi=sample, weights=weights)
