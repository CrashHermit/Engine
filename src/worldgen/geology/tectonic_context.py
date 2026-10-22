"""Continuous geological context for overlapping source-space region pairs."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.field.boundary_motion import BoundaryMotionSample
from src.worldgen.geology.config import MaterialBlendConfig, PolarityConfig
from src.worldgen.geology.crust_influence import (
    CrustInfluenceSample,
    continental_response_weight,
)
from src.worldgen.field.boundary_motion import BoundaryMotionGradientSample


from src.worldgen.geology.subduction_preference import overriding_weights


@dataclass(frozen=True, slots=True)
class TectonicContextSample:
    """Motion and material interpretation for active ordered region pairs."""

    plane_distance: np.ndarray
    continental_blend: np.ndarray
    b_overrides_weight: np.ndarray
    convergence: np.ndarray
    divergence: np.ndarray
    shear: np.ndarray
    influence: np.ndarray


@dataclass(frozen=True, slots=True)
class TectonicContextGradientSample:
    sample: TectonicContextSample
    plane_distance_gradients: np.ndarray
    continental_blend_gradients: np.ndarray
    b_overrides_weight_gradients: np.ndarray
    convergence_gradients: np.ndarray
    divergence_gradients: np.ndarray
    shear_gradients: np.ndarray
    influence_gradients: np.ndarray

    def __post_init__(self) -> None:
        for gradient in (
            self.plane_distance_gradients,
            self.continental_blend_gradients,
            self.b_overrides_weight_gradients,
            self.convergence_gradients,
            self.divergence_gradients,
            self.shear_gradients,
            self.influence_gradients,
        ):
            gradient.setflags(write=False)


@dataclass(frozen=True, slots=True)
class TectonicContextField:
    """Combine pair motion with injected crust and subduction-preference fields."""

    sample_material: Callable[[np.ndarray], CrustInfluenceSample]
    sample_preference: Callable[[np.ndarray], np.ndarray]
    pair_signs: np.ndarray
    directed: bool
    blend: MaterialBlendConfig = MaterialBlendConfig()
    polarity: PolarityConfig = PolarityConfig()
    sample_material_gradient: (
        Callable[[np.ndarray], tuple[CrustInfluenceSample, np.ndarray]] | None
    ) = None
    sample_preference_jacobian: (
        Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]] | None
    ) = None

    def __post_init__(self) -> None:
        pair_signs = np.array(self.pair_signs, dtype=np.float64, copy=True)
        pair_signs.setflags(write=False)
        object.__setattr__(self, "pair_signs", pair_signs)

    def _interpret_pairs(
        self,
        positions: np.ndarray,
        motion: BoundaryMotionSample,
        material_sample: CrustInfluenceSample | None,
        preference_vectors: np.ndarray | None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if len(motion.query_indices) == 0:
            empty = np.empty(0, dtype=np.float64)
            empty.setflags(write=False)
            return empty, empty

        materials = (
            self.sample_material(positions)
            if material_sample is None
            else material_sample
        )
        query_indices = motion.query_indices
        region_a = motion.region_pairs[:, 0]
        region_b = motion.region_pairs[:, 1]
        continental_blend = continental_response_weight(
            materials.continental_weight[query_indices], self.blend
        )
        if self.directed:
            vectors = (
                self.sample_preference(positions)
                if preference_vectors is None
                else preference_vectors
            )
            preference = np.einsum("ij,ij->i", vectors[query_indices], motion.normals)
        else:
            preference = np.zeros(len(query_indices), dtype=np.float64)
        b_overrides_weight = overriding_weights(
            preference,
            self.pair_signs[region_a, region_b],
            directed=self.directed,
            config=self.polarity,
        )
        continental_blend.setflags(write=False)
        b_overrides_weight.setflags(write=False)
        return continental_blend, b_overrides_weight

    def sample_pairs(
        self,
        positions: np.ndarray,
        motion: BoundaryMotionSample,
        *,
        material_sample: CrustInfluenceSample | None = None,
        preference_vectors: np.ndarray | None = None,
    ) -> TectonicContextSample:
        """Return per-pair response inputs using the original full query array."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(motion.query_indices) == 0:
            empty = np.empty(0, dtype=np.float64)
            empty.setflags(write=False)
            return TectonicContextSample(
                plane_distance=empty,
                continental_blend=empty,
                b_overrides_weight=empty,
                convergence=empty,
                divergence=empty,
                shear=empty,
                influence=empty,
            )

        continental_blend, b_overrides_weight = self._interpret_pairs(
            query_points, motion, material_sample, preference_vectors
        )
        return TectonicContextSample(
            plane_distance=motion.plane_distance,
            continental_blend=continental_blend,
            b_overrides_weight=b_overrides_weight,
            convergence=motion.convergence,
            divergence=motion.divergence,
            shear=motion.shear,
            influence=motion.influence,
        )

    def overriding_weights(
        self,
        positions: np.ndarray,
        motion: BoundaryMotionSample,
        *,
        material_sample: CrustInfluenceSample | None = None,
        preference_vectors: np.ndarray | None = None,
    ) -> np.ndarray:
        """Sample pair polarity using fields aligned to the full query positions."""
        query_points = np.asarray(positions, dtype=np.float64)
        return self._interpret_pairs(
            query_points, motion, material_sample, preference_vectors
        )[1]

    def sample_pairs_with_gradient(
        self,
        positions: np.ndarray,
        motion: BoundaryMotionGradientSample,
        *,
        material_sample: CrustInfluenceSample | None = None,
        material_gradient: np.ndarray | None = None,
        preference_vectors: np.ndarray | None = None,
        preference_jacobian: np.ndarray | None = None,
    ) -> TectonicContextGradientSample:
        """Interpret sparse motion/material pairs and their analytic gradients."""
        points = np.asarray(positions, dtype=np.float64)
        pair_motion = motion.sample
        if material_sample is None:
            material_sample, material_gradient = self.sample_material_gradient(points)
        if self.directed and preference_vectors is None:
            preference_vectors, preference_jacobian = self.sample_preference_jacobian(
                points
            )
        preference = preference_vectors
        preference_jacobians = preference_jacobian
        indices = pair_motion.query_indices
        a, b = (
            pair_motion.region_pairs.T
            if len(indices)
            else (np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64))
        )
        continental_x = (
            material_sample.continental_weight[indices] - self.blend.midpoint
        ) / self.blend.transition_width + 0.5
        clipped = np.clip(continental_x, 0.0, 1.0)
        continental_gradient = (
            6.0 * clipped * (1.0 - clipped) / self.blend.transition_width
        )[:, None] * material_gradient[indices]
        if self.directed:
            preference_dot = np.einsum(
                "ni,ni->n", preference[indices], pair_motion.normals
            )
            preference_gradient = np.einsum(
                "ni,nij->nj", pair_motion.normals, preference_jacobians[indices]
            )
        else:
            preference_dot = np.zeros(len(indices), dtype=np.float64)
            preference_gradient = np.zeros((len(indices), 3), dtype=np.float64)
        preference_scale = self.polarity.preference_scale
        scores = (
            preference_dot / preference_scale
            + self.polarity.seeded_bias * self.pair_signs[a, b]
        )
        parameter = np.clip((scores + 1.0) * 0.5, 0.0, 1.0)
        override_gradient = (3.0 * parameter * (1.0 - parameter) / preference_scale)[
            :, None
        ] * preference_gradient
        sample = self.sample_pairs(
            points,
            pair_motion,
            material_sample=material_sample,
            preference_vectors=preference,
        )
        return TectonicContextGradientSample(
            sample,
            motion.plane_distance_gradients,
            continental_gradient,
            override_gradient,
            motion.convergence_gradients,
            motion.divergence_gradients,
            motion.shear_gradients,
            motion.influence_gradients,
        )
