"""Mesh-independent composition of warped geological and world-space fields."""

from dataclasses import dataclass, field

import numpy as np

from src.worldgen.elevation.field import SourceElevationField
from src.worldgen.elevation.model import ElevationResult
from src.worldgen.elevation.variation import TerrainVariationField
from src.worldgen.field.compose import (
    SumScalarField,
    WarpedScalarField,
    WarpedVectorField,
)
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.warp import ShearWarpField
from src.worldgen.geology.field import GeologyField
from src.worldgen.geology.model import GeologyResult
from src.worldgen.geometry.differential import pullback_normals, pullback_vectors


@dataclass(frozen=True, slots=True)
class WorldSample:
    """Dense geological and elevation values for one arbitrary query batch."""

    geology: GeologyResult
    elevation: ElevationResult


@dataclass(frozen=True, slots=True)
class WorldBoundaryVectorSample:
    """All active pairs with world-space normals and transported velocities.

    Influence and signed plane distance retain their source-space meaning;
    they are not recomputed as Euclidean distances in the warped coordinates.
    """

    query_indices: np.ndarray
    region_pairs: np.ndarray
    influence: np.ndarray
    source_plane_distance: np.ndarray
    normals: np.ndarray
    vectors: np.ndarray


@dataclass(frozen=True, slots=True)
class WorldField:
    """Evaluate coherent geology and elevation at arbitrary Cartesian positions."""

    geology: GeologyField
    source_elevation: SourceElevationField
    variation: TerrainVariationField
    warp: ShearWarpField
    elevation: SumScalarField = field(init=False, repr=False)
    convergence: WarpedScalarField = field(init=False, repr=False)
    divergence: WarpedScalarField = field(init=False, repr=False)
    shear: WarpedScalarField = field(init=False, repr=False)
    coastal_relief: WarpedScalarField = field(init=False, repr=False)
    tectonic_relief: WarpedScalarField = field(init=False, repr=False)
    convergent_relief: WarpedScalarField = field(init=False, repr=False)
    divergent_relief: WarpedScalarField = field(init=False, repr=False)
    transform_relief: WarpedScalarField = field(init=False, repr=False)
    volcanic_relief: WarpedScalarField = field(init=False, repr=False)
    shear_relief: WarpedScalarField = field(init=False, repr=False)
    region_velocity: WarpedVectorField = field(init=False, repr=False)

    def __post_init__(self) -> None:
        warp_sample = self.warp.sample
        warp_jacobian = self.warp.sample_with_jacobian
        source_elevation = WarpedScalarField(
            warp_sample,
            self.source_elevation.sample_total_source,
            warp_jacobian,
            self.source_elevation.sample_total_source_with_gradient,
        )
        object.__setattr__(
            self,
            "elevation",
            SumScalarField(
                (source_elevation.sample, self.variation.sample_fraction),
                (
                    source_elevation.sample_with_gradient,
                    self.variation.sample_fraction_with_gradient,
                ),
            ),
        )
        object.__setattr__(
            self,
            "region_velocity",
            WarpedVectorField(
                warp_jacobian, self.geology.motion.vectors.sample_owner_vectors
            ),
        )
        for name, sampler, gradient_sampler in (
            (
                "convergence",
                self.geology.interaction.sample_convergence,
                self.geology.interaction.sample_convergence_with_gradient,
            ),
            (
                "divergence",
                self.geology.interaction.sample_divergence,
                self.geology.interaction.sample_divergence_with_gradient,
            ),
            (
                "shear",
                self.geology.interaction.sample_shear,
                self.geology.interaction.sample_shear_with_gradient,
            ),
            (
                "coastal_relief",
                self.source_elevation.coastal.sample_elevation,
                self.source_elevation.coastal.sample_with_gradient,
            ),
            (
                "tectonic_relief",
                self.source_elevation.tectonic.sample,
                self.source_elevation.tectonic.sample_with_gradient,
            ),
            (
                "convergent_relief",
                self.source_elevation.convergent.sample,
                self.source_elevation.convergent.sample_with_gradient,
            ),
            (
                "divergent_relief",
                self.source_elevation.divergent.sample,
                self.source_elevation.divergent.sample_with_gradient,
            ),
            (
                "transform_relief",
                self.source_elevation.transform.sample,
                self.source_elevation.transform.sample_with_gradient,
            ),
            (
                "shear_relief",
                self.source_elevation.shear.sample,
                self.source_elevation.shear.sample_with_gradient,
            ),
            (
                "volcanic_relief",
                lambda positions: (
                    self.source_elevation.volcanism.sample(positions).relief
                ),
                lambda positions: (
                    self.source_elevation.volcanism.sample_with_gradient(
                        positions
                    ).relief
                ),
            ),
        ):
            object.__setattr__(
                self,
                name,
                WarpedScalarField(
                    warp_sample, sampler, warp_jacobian, gradient_sampler
                ),
            )

    def sample_world(self, positions: np.ndarray) -> WorldSample:
        """Sample the completed fields without tying them to a mesh or radius."""
        world_positions = np.asarray(positions, dtype=np.float64)
        query_count = len(world_positions)
        geology_result = GeologyResult(
            plate_ids=np.empty(query_count, dtype=np.int64),
            crust_region_ids=np.empty(query_count, dtype=np.int64),
            continental_mask=np.empty(query_count, dtype=np.bool_),
            continental_weight=np.empty(query_count, dtype=np.float64),
            subduction_preference_strength=np.empty(query_count, dtype=np.float64),
            max_plate_weight=np.empty(query_count, dtype=np.float64),
            region_overlap=np.empty(query_count, dtype=np.float64),
            convergence=np.empty(query_count, dtype=np.float64),
            divergence=np.empty(query_count, dtype=np.float64),
            shear=np.empty(query_count, dtype=np.float64),
        )
        elevation_result = ElevationResult(
            coastal_elevation=np.empty(query_count, dtype=np.float64),
            volcanic_potential=np.empty(query_count, dtype=np.float64),
            volcanic_strength=np.empty(query_count, dtype=np.float64),
            convergent_relief=np.empty(query_count, dtype=np.float64),
            divergent_relief=np.empty(query_count, dtype=np.float64),
            transform_relief=np.empty(query_count, dtype=np.float64),
            shear_relief=np.empty(query_count, dtype=np.float64),
            tectonic_relief=np.empty(query_count, dtype=np.float64),
            terrain_variation=np.empty(query_count, dtype=np.float64),
            volcanic_relief=np.empty(query_count, dtype=np.float64),
            elevation=np.empty(query_count, dtype=np.float64),
        )

        for start in range(0, query_count, 1024):
            stop = min(start + 1024, query_count)
            world_block = world_positions[start:stop]
            source_block = self.warp.sample(world_block)
            geology_sample = self.geology.sample_source(source_block)
            source_sample = self.source_elevation.sample_source(
                source_block, geology_sample=geology_sample
            )
            terrain_variation = self.variation.sample_fraction(world_block)
            base_elevation = source_sample.total
            values = geology_sample.result
            geology_result.plate_ids[start:stop] = values.plate_ids
            geology_result.crust_region_ids[start:stop] = values.crust_region_ids
            geology_result.continental_mask[start:stop] = values.continental_mask
            geology_result.continental_weight[start:stop] = values.continental_weight
            geology_result.subduction_preference_strength[start:stop] = (
                values.subduction_preference_strength
            )
            geology_result.max_plate_weight[start:stop] = values.max_plate_weight
            geology_result.region_overlap[start:stop] = values.region_overlap
            geology_result.convergence[start:stop] = values.convergence
            geology_result.divergence[start:stop] = values.divergence
            geology_result.shear[start:stop] = values.shear
            elevation_result.coastal_elevation[start:stop] = (
                source_sample.coastal_elevation
            )
            elevation_result.convergent_relief[start:stop] = (
                source_sample.convergent_relief
            )
            elevation_result.divergent_relief[start:stop] = (
                source_sample.divergent_relief
            )
            elevation_result.transform_relief[start:stop] = (
                source_sample.transform_relief
            )
            elevation_result.shear_relief[start:stop] = source_sample.shear_relief
            elevation_result.tectonic_relief[start:stop] = source_sample.tectonic_relief
            elevation_result.volcanic_potential[start:stop] = (
                source_sample.volcanic_potential
            )
            elevation_result.volcanic_strength[start:stop] = (
                source_sample.volcanic_strength
            )
            elevation_result.volcanic_relief[start:stop] = source_sample.volcanic_relief
            elevation_result.terrain_variation[start:stop] = terrain_variation
            elevation_result.elevation[start:stop] = base_elevation + terrain_variation

        for values in (
            geology_result.plate_ids,
            geology_result.crust_region_ids,
            geology_result.continental_mask,
            geology_result.continental_weight,
            geology_result.subduction_preference_strength,
            geology_result.max_plate_weight,
            geology_result.region_overlap,
            geology_result.convergence,
            geology_result.divergence,
            geology_result.shear,
            elevation_result.coastal_elevation,
            elevation_result.convergent_relief,
            elevation_result.divergent_relief,
            elevation_result.transform_relief,
            elevation_result.shear_relief,
            elevation_result.tectonic_relief,
            elevation_result.volcanic_potential,
            elevation_result.volcanic_strength,
            elevation_result.volcanic_relief,
            elevation_result.terrain_variation,
            elevation_result.elevation,
        ):
            values.setflags(write=False)
        return WorldSample(geology_result, elevation_result)

    def sample_elevation_meters(
        self, positions: np.ndarray, *, radius_m: float
    ) -> np.ndarray:
        """Sample radius-fraction elevation and convert it to meters."""
        elevation_m = self.elevation.sample(positions) * radius_m
        elevation_m.setflags(write=False)
        return elevation_m

    def sample_elevation_meters_with_gradient(
        self, positions: np.ndarray, *, radius_m: float
    ) -> ScalarSample:
        """Return height in meters and its gradient per unit Cartesian coordinate."""
        sample = self.elevation.sample_with_gradient(positions)
        return ScalarSample(sample.values * radius_m, sample.gradients * radius_m)

    def sample_boundary_vectors(
        self, positions: np.ndarray
    ) -> WorldBoundaryVectorSample:
        """Query all locally overlapping pairs without requiring caller region IDs.

        This exposes transported vectors for other consumers. Construction C
        still computes geological interactions entirely in source coordinates.
        """
        transformed = self.warp.sample_with_jacobian(
            np.asarray(positions, dtype=np.float64)
        )
        source = self.geology.motion.vectors.sample(transformed.values)
        jacobians = transformed.jacobians[source.query_indices]
        return WorldBoundaryVectorSample(
            query_indices=source.query_indices,
            region_pairs=source.region_pairs,
            influence=source.influence,
            source_plane_distance=source.plane_distance,
            normals=pullback_normals(source.normals, jacobians),
            vectors=pullback_vectors(source.vectors, jacobians[:, None, :, :]),
        )
