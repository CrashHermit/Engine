"""Mesh-independent composition of warped geological and world-space fields."""

from dataclasses import dataclass, field

import numpy as np

from src.worldgen.climate.field import ClimateField
from src.worldgen.climate.model import ClimateSample
from src.worldgen.relief.composition import ElevationField
from src.worldgen.relief.field import SourceReliefField
from src.worldgen.relief.impact import ImpactField
from src.worldgen.relief.model import ElevationResult
from src.worldgen.relief.variation import TerrainVariationField
from src.worldgen.relief.volcanism import VolcanicField
from src.worldgen.field.compose import (
    WarpedScalarField,
    ReparameterizedVectorField,
)
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.warp import ShearWarpField
from src.worldgen.geology.field import GeologyField
from src.worldgen.geology.model import GeologyResult


@dataclass(frozen=True, slots=True)
class WorldSample:
    """Geological, elevation, and climate values at arbitrary query positions."""

    geology: GeologyResult
    elevation: ElevationResult
    climate: ClimateSample


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
    """Evaluate coherent geology, elevation, and climate at Cartesian positions."""

    geology: GeologyField
    source_relief: SourceReliefField
    variation: TerrainVariationField
    warp: ShearWarpField
    impact_relief: ImpactField
    volcanism: VolcanicField
    climate: ClimateField
    elevation: ElevationField = field(init=False, repr=False)
    convergence: WarpedScalarField = field(init=False, repr=False)
    divergence: WarpedScalarField = field(init=False, repr=False)
    shear: WarpedScalarField = field(init=False, repr=False)
    coastal_relief: WarpedScalarField = field(init=False, repr=False)
    tectonic_relief: WarpedScalarField = field(init=False, repr=False)
    convergent_relief: WarpedScalarField = field(init=False, repr=False)
    divergent_relief: WarpedScalarField = field(init=False, repr=False)
    transform_relief: WarpedScalarField = field(init=False, repr=False)
    shear_relief: WarpedScalarField = field(init=False, repr=False)
    region_velocity: ReparameterizedVectorField = field(init=False, repr=False)

    def __post_init__(self) -> None:
        warp_sample = self.warp.sample
        warp_jacobian = self.warp.sample_with_jacobian
        object.__setattr__(
            self,
            "elevation",
            ElevationField(
                source_relief=self.source_relief,
                warp=self.warp,
                volcanism=self.volcanism,
                impact_relief=self.impact_relief,
                variation=self.variation,
            ),
        )
        object.__setattr__(
            self,
            "region_velocity",
            ReparameterizedVectorField(
                warp_sample,
                self.geology.motion.vectors.sample_owner_vectors,
                warp_jacobian,
                self.geology.motion.vectors.sample_owner_vectors_with_jacobian,
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
                self.source_relief.coastal.sample_elevation,
                self.source_relief.coastal.sample_with_gradient,
            ),
            (
                "tectonic_relief",
                self.source_relief.tectonic.sample,
                self.source_relief.tectonic.sample_with_gradient,
            ),
            (
                "convergent_relief",
                self.source_relief.convergent.sample,
                self.source_relief.convergent.sample_with_gradient,
            ),
            (
                "divergent_relief",
                self.source_relief.divergent.sample,
                self.source_relief.divergent.sample_with_gradient,
            ),
            (
                "transform_relief",
                self.source_relief.transform.sample,
                self.source_relief.transform.sample_with_gradient,
            ),
            (
                "shear_relief",
                self.source_relief.shear.sample,
                self.source_relief.shear.sample_with_gradient,
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
        elevation_arrays = {
            name: np.empty(query_count, dtype=np.float64)
            for name in (
                "coastal_elevation",
                "volcanic_strength",
                "convergent_relief",
                "divergent_relief",
                "transform_relief",
                "shear_relief",
                "tectonic_relief",
                "terrain_variation",
                "volcanic_relief",
                "impact_relief",
                "elevation",
            )
        }

        for start in range(0, query_count, 1024):
            stop = min(start + 1024, query_count)
            world_block = world_positions[start:stop]
            source_block = self.warp.sample(world_block)
            geology_sample = self.geology.sample_source(source_block)
            elevation_block = self.elevation.sample_components(
                world_block,
                source_positions=source_block,
                relief_inputs=geology_sample.to_relief_inputs(),
            )
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
            for name in elevation_arrays:
                elevation_arrays[name][start:stop] = getattr(elevation_block, name)

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
            *elevation_arrays.values(),
        ):
            values.setflags(write=False)
        elevation_result = ElevationResult(**elevation_arrays)
        return WorldSample(
            geology_result, elevation_result, self.climate.sample(world_positions)
        )

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
        """Return the same transported pair vectors and normals used by geology."""
        source_positions = self.warp.sample(np.asarray(positions, dtype=np.float64))
        transported = self.geology.motion.vectors.sample(source_positions)
        return WorldBoundaryVectorSample(
            query_indices=transported.query_indices,
            region_pairs=transported.region_pairs,
            influence=transported.influence,
            source_plane_distance=transported.plane_distance,
            normals=transported.normals,
            vectors=transported.vectors,
        )
