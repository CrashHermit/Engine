"""Continuous, mesh-independent geological field composition."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.boundary_motion import (
    BoundaryMotionField,
    BoundaryMotionSample,
)
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.interaction import BoundaryInteractionField
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.noise import noise_multiplier, noise_multiplier_with_gradient
from src.worldgen.field.region_influence import RegionInfluenceField
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.geology.config import CrustDensityConfig
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.geology.crust_influence import CrustInfluenceField
from src.worldgen.geology.model import (
    GeologyGradientSample,
    GeologyResult,
    GeologySample,
)
from src.worldgen.geology.subduction_preference import SubductionPreferenceField
from src.worldgen.geology.tectonic_context import (
    TectonicContextField,
    TectonicContextSample,
)


@dataclass(frozen=True, slots=True)
class GeologyField:
    """Shared continuous geological inputs and source-space query operations."""

    regions: WarpedVoronoiField
    plate_influence: RegionInfluenceField
    crust: CrustField
    crust_influence: RegionInfluenceField
    material: CrustInfluenceField
    preference: SubductionPreferenceField
    rotations: RegionRotationField
    overlap: RegionOverlapField
    motion: BoundaryMotionField
    interaction: BoundaryInteractionField
    context: TectonicContextField
    density_config: CrustDensityConfig
    density_noise_seed: int

    def sample_source(self, positions: np.ndarray) -> GeologySample:
        """Evaluate shared source-space ownership, motion, and interactions once."""
        query_points = np.asarray(positions, dtype=np.float64)
        query_count = len(query_points)
        if query_count == 0:
            return _empty_geology_sample()

        plate_regions = self.plate_influence.sample(query_points)
        overlap_sample = self.overlap.sample_from_regions(plate_regions)
        motion_sample = self.motion.sample_from_overlap(query_points, overlap_sample)
        crust_regions = self.crust_influence.sample(query_points)
        material_sample = self.material.sample_from_regions(crust_regions)
        preference_vectors = self.preference.sample_from_regions(
            query_points, crust_regions
        )
        context_sample = self.context.sample_pairs(
            query_points,
            motion_sample,
            material_sample=material_sample,
            preference_vectors=preference_vectors,
        )
        interactions = self.interaction.sample_from_motion(query_count, motion_sample)
        region_overlap = np.bincount(
            motion_sample.query_indices,
            weights=motion_sample.influence,
            minlength=query_count,
        ).astype(np.float64, copy=False)
        plate_ids = plate_regions.voronoi.owner_seed_id
        crust_region_ids = crust_regions.voronoi.owner_seed_id
        continental_mask = self.crust.continental_regions[crust_region_ids]
        preference_strength = np.linalg.norm(preference_vectors, axis=1)
        max_plate_weight = np.max(plate_regions.weights, axis=1)
        arrays = (
            plate_ids,
            crust_region_ids,
            continental_mask,
            material_sample.continental_weight,
            preference_strength,
            max_plate_weight,
            region_overlap,
            interactions.convergence,
            interactions.divergence,
            interactions.shear,
        )
        for values in arrays:
            values.setflags(write=False)
        result = GeologyResult(
            plate_ids=plate_ids,
            crust_region_ids=crust_region_ids,
            continental_mask=continental_mask,
            continental_weight=material_sample.continental_weight,
            subduction_preference_strength=preference_strength,
            max_plate_weight=max_plate_weight,
            region_overlap=region_overlap,
            convergence=interactions.convergence,
            divergence=interactions.divergence,
            shear=interactions.shear,
        )
        return GeologySample(result, motion_sample, context_sample)

    def sample_continental_weight_with_gradient(
        self, positions: np.ndarray
    ) -> ScalarSample:
        material, gradients = self.material.sample_with_gradient(positions)
        return ScalarSample(material.continental_weight, gradients)

    def sample_source_with_gradient(
        self, positions: np.ndarray
    ) -> GeologyGradientSample:
        points = np.asarray(positions, dtype=np.float64)
        query_count = len(points)
        if query_count == 0:
            empty = self.sample_source(points)
            motion_gradient = self.motion.sample_with_gradient(points)
            context_gradient = self.context.sample_pairs_with_gradient(
                points, motion_gradient
            )
            _, gradients = self.material.sample_with_gradient(points)
            return GeologyGradientSample(
                empty, motion_gradient, context_gradient, gradients
            )

        plate_regions, plate_membership_gradients = (
            self.plate_influence.sample_with_gradient(points)
        )
        overlap = self.overlap.sample_from_regions(plate_regions)
        motion_gradient = self.motion.sample_from_regions_with_gradient(
            points, plate_regions, plate_membership_gradients, overlap_sample=overlap
        )
        motion_sample = motion_gradient.sample
        crust_regions, crust_membership_gradients = (
            self.crust_influence.sample_with_gradient(points)
        )
        material_sample, material_gradients = (
            self.material.sample_from_regions_with_gradient(
                crust_regions, crust_membership_gradients
            )
        )
        preference_vectors, preference_jacobians = self.preference.sample_with_jacobian(
            points, crust_regions, crust_membership_gradients
        )
        context_gradient = self.context.sample_pairs_with_gradient(
            points,
            motion_gradient,
            material_sample=material_sample,
            material_gradient=material_gradients,
            preference_vectors=preference_vectors,
            preference_jacobian=preference_jacobians,
        )
        interactions = self.interaction.sample_from_motion(query_count, motion_sample)
        region_overlap = np.bincount(
            motion_sample.query_indices,
            weights=motion_sample.influence,
            minlength=query_count,
        ).astype(np.float64, copy=False)
        plate_ids = plate_regions.voronoi.owner_seed_id
        crust_region_ids = crust_regions.voronoi.owner_seed_id
        continental_mask = self.crust.continental_regions[crust_region_ids]
        preference_strength = np.linalg.norm(preference_vectors, axis=1)
        max_plate_weight = np.max(plate_regions.weights, axis=1)
        arrays = (
            plate_ids,
            crust_region_ids,
            continental_mask,
            material_sample.continental_weight,
            preference_strength,
            max_plate_weight,
            region_overlap,
            interactions.convergence,
            interactions.divergence,
            interactions.shear,
        )
        for values in arrays:
            values.setflags(write=False)
        result = GeologyResult(
            plate_ids=plate_ids,
            crust_region_ids=crust_region_ids,
            continental_mask=continental_mask,
            continental_weight=material_sample.continental_weight,
            subduction_preference_strength=preference_strength,
            max_plate_weight=max_plate_weight,
            region_overlap=region_overlap,
            convergence=interactions.convergence,
            divergence=interactions.divergence,
            shear=interactions.shear,
        )
        sample = GeologySample(result, motion_sample, context_gradient.sample)
        return GeologyGradientSample(
            sample, motion_gradient, context_gradient, material_gradients
        )

    def sample_density_anomaly_with_gradient(
        self, positions: np.ndarray
    ) -> ScalarSample:
        sample = noise_multiplier_with_gradient(
            np.asarray(positions, dtype=np.float64),
            seed=self.density_noise_seed,
            frequency=self.density_config.noise_frequency,
            strength=self.density_config.variation_strength,
        )
        values = sample.values - 1.0
        values.setflags(write=False)
        return ScalarSample(values, sample.gradients)

    def sample_density_anomaly(self, positions: np.ndarray) -> np.ndarray:
        """Sample the independent relative crust-density anomaly."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(query_points) == 0:
            values = np.empty(0, dtype=np.float64)
        else:
            values = (
                noise_multiplier(
                    query_points,
                    seed=self.density_noise_seed,
                    frequency=self.density_config.noise_frequency,
                    strength=self.density_config.variation_strength,
                )
                - 1.0
            )
        values.setflags(write=False)
        return values


def _empty_geology_sample() -> GeologySample:
    empty_float = np.empty(0, dtype=np.float64)
    empty_ids = np.empty(0, dtype=np.int64)
    empty_pairs = np.empty((0, 2), dtype=np.int64)
    empty_vectors = np.empty((0, 3), dtype=np.float64)
    for values in (empty_float, empty_ids, empty_pairs, empty_vectors):
        values.setflags(write=False)
    motion = BoundaryMotionSample(
        query_indices=empty_ids,
        region_pairs=empty_pairs,
        plane_distance=empty_float,
        influence=empty_float,
        normals=empty_vectors,
        opening=empty_float,
        convergence=empty_float,
        divergence=empty_float,
        shear=empty_float,
    )
    context = TectonicContextSample(
        plane_distance=empty_float,
        continental_blend=empty_float,
        b_overrides_weight=empty_float,
        convergence=empty_float,
        divergence=empty_float,
        shear=empty_float,
        influence=empty_float,
    )
    result = GeologyResult(
        plate_ids=empty_ids,
        crust_region_ids=empty_ids,
        continental_mask=np.empty(0, dtype=np.bool_),
        continental_weight=empty_float,
        subduction_preference_strength=empty_float,
        max_plate_weight=empty_float,
        region_overlap=empty_float,
        convergence=empty_float,
        divergence=empty_float,
        shear=empty_float,
    )
    result.continental_mask.setflags(write=False)
    return GeologySample(result, motion, context)
