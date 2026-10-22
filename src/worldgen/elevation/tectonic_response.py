"""Compose source-space tectonic relief from interpreted boundary context.

The raw relief profiles retain local shape falloff without pair weighting.
This module applies overlap influence once before the generic pair reduction.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample

from src.worldgen.elevation.config import SourceReliefConfig, TectonicResponseConfig
from src.worldgen.elevation.profiles import (
    collision_profile_with_partials,
    divergent_profile_with_partials,
    subduction_profile_with_partials,
    transform_profile_with_partials,
)
from src.worldgen.elevation.response import (
    collision_relief,
    continental_rift_relief,
    oceanic_ridge_relief,
    shear_relief,
    subduction_relief,
    transform_relief,
)
from src.worldgen.elevation.shear import shear_strength
from src.worldgen.elevation.transform import transform_strength
from src.worldgen.field.boundary_motion import (
    BoundaryMotionGradientSample,
    BoundaryMotionSample,
)
from src.worldgen.geology.tectonic_context import (
    TectonicContextGradientSample,
    TectonicContextSample,
)
from src.worldgen.elevation.ridge_detail import RidgeDetailField


def blend_subduction_orientations(
    plane_distance: np.ndarray,
    convergence: np.ndarray,
    b_overrides_weight: np.ndarray,
    influence: np.ndarray,
    *,
    config: SourceReliefConfig,
    arc_height_multiplier: float,
    trench_depth_multiplier: float,
    detail_weights: np.ndarray | None = None,
    detail_strength: float = 0.0,
) -> np.ndarray:
    """Blend explicitly configured trench/arc profiles and apply pair overlap."""
    toward_b = subduction_relief(
        plane_distance,
        convergence,
        config.width_fraction,
        config.height_fraction,
        arc_height_multiplier=arc_height_multiplier,
        trench_depth_multiplier=trench_depth_multiplier,
    )
    if detail_weights is not None and detail_strength != 0.0:
        trench = subduction_relief(
            plane_distance,
            convergence,
            config.width_fraction,
            config.height_fraction,
            arc_height_multiplier=0.0,
            trench_depth_multiplier=trench_depth_multiplier,
        )
        toward_b = trench + (toward_b - trench) * (
            1.0 + detail_strength * (2.0 * detail_weights - 1.0)
        )
    toward_a = subduction_relief(
        -plane_distance,
        convergence,
        config.width_fraction,
        config.height_fraction,
        arc_height_multiplier=arc_height_multiplier,
        trench_depth_multiplier=trench_depth_multiplier,
    )
    if detail_weights is not None and detail_strength != 0.0:
        trench = subduction_relief(
            -plane_distance,
            convergence,
            config.width_fraction,
            config.height_fraction,
            arc_height_multiplier=0.0,
            trench_depth_multiplier=trench_depth_multiplier,
        )
        toward_a = trench + (toward_a - trench) * (
            1.0 + detail_strength * (2.0 * detail_weights - 1.0)
        )
    return (
        b_overrides_weight * toward_b + (1.0 - b_overrides_weight) * toward_a
    ) * influence


def convergent_relief(
    plane_distance: np.ndarray,
    convergence: np.ndarray,
    b_overrides_weight: np.ndarray,
    influence: np.ndarray,
    continental_blend: np.ndarray,
    *,
    config: TectonicResponseConfig = TectonicResponseConfig(),
    ridge_weights: np.ndarray | None = None,
    ridge_blend: float = 0.0,
    arc_detail_strength: float = 0.0,
) -> np.ndarray:
    """Blend continental collision and polarity-oriented subduction relief."""
    collision_profile = (
        collision_relief(
            np.abs(plane_distance),
            convergence,
            config.collision.width_fraction,
            config.collision.height_fraction,
            crest_width_fraction=config.collision_crest_width_fraction,
        )
        * influence
    )
    if ridge_weights is not None and ridge_blend != 0.0:
        broad = (
            collision_relief(
                np.abs(plane_distance),
                convergence,
                config.collision.width_fraction,
                config.collision.height_fraction,
                crest_height_multiplier=0.0,
            )
            * influence
        )
        collision_profile = (
            1.0 - ridge_blend
        ) * collision_profile + ridge_blend * broad * (1.0 + 2.0 * ridge_weights)
    subduction_profile = blend_subduction_orientations(
        plane_distance,
        convergence,
        b_overrides_weight,
        influence,
        config=config.subduction,
        detail_weights=ridge_weights,
        arc_height_multiplier=config.subduction_arc_height_multiplier,
        detail_strength=arc_detail_strength,
        trench_depth_multiplier=config.subduction_trench_depth_multiplier,
    )
    return (
        continental_blend * collision_profile
        + (1.0 - continental_blend) * subduction_profile
    )


def divergent_relief(
    plane_distance: np.ndarray,
    divergence: np.ndarray,
    influence: np.ndarray,
    continental_blend: np.ndarray,
    *,
    config: TectonicResponseConfig = TectonicResponseConfig(),
    detail_weights: np.ndarray | None = None,
    ridge_detail_strength: float = 0.0,
    rift_detail_strength: float = 0.0,
) -> np.ndarray:
    """Blend continental rift and oceanic ridge relief in source space."""
    distance = np.abs(plane_distance)
    rift_profile = continental_rift_relief(
        distance,
        divergence,
        config.rift.width_fraction,
        config.rift.height_fraction,
    )
    ridge_profile = oceanic_ridge_relief(
        distance,
        divergence,
        config.ridge.width_fraction,
        config.ridge.height_fraction,
        axial_width_fraction=config.ridge_axial_width_fraction,
    )
    if detail_weights is not None:
        signed_detail = 2.0 * detail_weights - 1.0
        # Isolate positive rift shoulders; axial subsidence is untouched.
        shoulders = continental_rift_relief(
            distance,
            divergence,
            config.rift.width_fraction,
            config.rift.height_fraction,
            axial_depth_multiplier=0.0,
        )
        rift_profile = rift_profile + rift_detail_strength * shoulders * signed_detail
        # Preserve the full axial feature; vary only the outer ridge flanks.
        axial_width = config.ridge.width_fraction * config.ridge_axial_width_fraction
        outer = np.clip((distance - axial_width) / axial_width, 0.0, 1.0)
        outer = outer * outer * (3.0 - 2.0 * outer)
        ridge_profile = ridge_profile * (
            1.0 + ridge_detail_strength * outer * signed_detail
        )
    return (
        continental_blend * rift_profile + (1.0 - continental_blend) * ridge_profile
    ) * influence


def transform_boundary_relief(
    plane_distance: np.ndarray,
    closing: np.ndarray,
    shear: np.ndarray,
    influence: np.ndarray,
    *,
    smoothing: float,
    config: SourceReliefConfig = SourceReliefConfig(
        width_percent=3.6, height_percent=0.00785
    ),
    detail_weights: np.ndarray | None = None,
    detail_strength: float = 0.0,
) -> np.ndarray:
    """Return compact oblique transform uplift or subsidence at boundary pairs."""
    strength = transform_strength(closing, shear, smoothing=smoothing)
    if detail_weights is not None:
        strength = strength * (1.0 + detail_strength * (2.0 * detail_weights - 1.0))
    return (
        transform_relief(
            np.abs(plane_distance),
            strength,
            config.width_fraction,
            config.height_fraction,
        )
        * influence
    )


def shear_boundary_relief(
    plane_distance: np.ndarray,
    closing: np.ndarray,
    shear: np.ndarray,
    influence: np.ndarray,
    *,
    smoothing: float,
    config: SourceReliefConfig = SourceReliefConfig(
        width_percent=3.6, height_percent=0.00392
    ),
    detail_weights: np.ndarray | None = None,
    detail_strength: float = 0.0,
) -> np.ndarray:
    """Return compact residual pure-shear relief at boundary pairs."""
    strength = shear_strength(closing, shear, smoothing=smoothing)
    if detail_weights is not None:
        strength = strength * (1.0 + detail_strength * (2.0 * detail_weights - 1.0))
    return (
        shear_relief(
            np.abs(plane_distance),
            strength,
            config.width_fraction,
            config.height_fraction,
        )
        * influence
    )


@dataclass(frozen=True, slots=True)
class TectonicReliefSample:
    """Named additive geological responses for one query block."""

    convergent: np.ndarray
    divergent: np.ndarray
    transform: np.ndarray
    shear: np.ndarray
    total: np.ndarray


@dataclass(frozen=True, slots=True)
class TectonicResponseGradientSample:
    """Analytic Cartesian gradients for each additive tectonic response."""

    convergent: ScalarSample
    divergent: ScalarSample
    transform: ScalarSample
    shear: ScalarSample
    total: ScalarSample


@dataclass(frozen=True, slots=True)
class TectonicResponseSampler:
    """Evaluate additive relief from an injected geological context sampler."""

    sample_context: Callable[[np.ndarray, BoundaryMotionSample], TectonicContextSample]
    config: TectonicResponseConfig = TectonicResponseConfig()
    ridge_detail: RidgeDetailField | None = None
    sample_context_with_gradient: (
        Callable[
            [np.ndarray, BoundaryMotionGradientSample],
            TectonicContextGradientSample,
        ]
        | None
    ) = None

    def sample_convergent(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray:
        """Sample only collision and subduction relief from boundary context."""
        context = self.sample_context(positions, motion)
        return convergent_relief(
            context.plane_distance,
            context.convergence,
            context.b_overrides_weight,
            context.influence,
            context.continental_blend,
            config=self.config,
            ridge_weights=(
                self.ridge_detail.sample(positions)[motion.query_indices]
                if self.ridge_detail is not None
                else None
            ),
            ridge_blend=self.ridge_detail.config.blend if self.ridge_detail else 0.0,
            arc_detail_strength=self.ridge_detail.config.arc_strength
            if self.ridge_detail
            else 0.0,
        )

    def sample_divergent(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray:
        """Sample only rift and ridge relief from boundary context."""
        context = self.sample_context(positions, motion)
        return divergent_relief(
            context.plane_distance,
            context.divergence,
            context.influence,
            context.continental_blend,
            config=self.config,
            detail_weights=self._detail_weights(positions, motion),
            ridge_detail_strength=self.ridge_detail.config.ridge_strength
            if self.ridge_detail
            else 0.0,
            rift_detail_strength=self.ridge_detail.config.rift_strength
            if self.ridge_detail
            else 0.0,
        )

    def sample_transform(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray:
        """Sample only the compact oblique-transform contribution."""
        context = self.sample_context(positions, motion)
        return transform_boundary_relief(
            context.plane_distance,
            context.convergence - context.divergence,
            context.shear,
            context.influence,
            config=self.config.transform,
            smoothing=self.config.motion_smoothing_width,
            detail_weights=self._detail_weights(positions, motion),
            detail_strength=self.ridge_detail.config.transform_strength
            if self.ridge_detail
            else 0.0,
        )

    def sample_shear(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray:
        """Sample only residual pure-shear fault relief."""
        context = self.sample_context(positions, motion)
        return shear_boundary_relief(
            context.plane_distance,
            context.convergence - context.divergence,
            context.shear,
            context.influence,
            config=self.config.shear,
            smoothing=self.config.motion_smoothing_width,
            detail_weights=self._detail_weights(positions, motion),
            detail_strength=self.ridge_detail.config.shear_strength
            if self.ridge_detail
            else 0.0,
        )

    def _detail_weights(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray | None:
        return (
            self.ridge_detail.sample(positions)[motion.query_indices]
            if self.ridge_detail is not None
            else None
        )

    def sample_from_context(
        self, context: TectonicContextSample, *, ridge_weights: np.ndarray | None = None
    ) -> TectonicReliefSample:
        """Evaluate each independent relief profile from an existing context."""
        closing = context.convergence - context.divergence
        convergent = convergent_relief(
            context.plane_distance,
            context.convergence,
            context.b_overrides_weight,
            context.influence,
            context.continental_blend,
            config=self.config,
            ridge_weights=ridge_weights,
            ridge_blend=self.ridge_detail.config.blend if self.ridge_detail else 0.0,
            arc_detail_strength=self.ridge_detail.config.arc_strength
            if self.ridge_detail
            else 0.0,
        )
        divergent = divergent_relief(
            context.plane_distance,
            context.divergence,
            context.influence,
            context.continental_blend,
            config=self.config,
            detail_weights=ridge_weights,
            ridge_detail_strength=self.ridge_detail.config.ridge_strength
            if self.ridge_detail
            else 0.0,
            rift_detail_strength=self.ridge_detail.config.rift_strength
            if self.ridge_detail
            else 0.0,
        )
        transform = transform_boundary_relief(
            context.plane_distance,
            closing,
            context.shear,
            context.influence,
            config=self.config.transform,
            smoothing=self.config.motion_smoothing_width,
            detail_weights=ridge_weights,
            detail_strength=self.ridge_detail.config.transform_strength
            if self.ridge_detail
            else 0.0,
        )
        shear = shear_boundary_relief(
            context.plane_distance,
            closing,
            context.shear,
            context.influence,
            config=self.config.shear,
            smoothing=self.config.motion_smoothing_width,
            detail_weights=ridge_weights,
            detail_strength=self.ridge_detail.config.shear_strength
            if self.ridge_detail
            else 0.0,
        )
        total = ((convergent + divergent) + transform) + shear
        for values in (convergent, divergent, transform, shear, total):
            values.setflags(write=False)
        return TectonicReliefSample(
            convergent=convergent,
            divergent=divergent,
            transform=transform,
            shear=shear,
            total=total,
        )

    def sample_from_context_with_gradient(
        self,
        context: TectonicContextGradientSample,
        *,
        ridge_weights: ScalarSample | None = None,
    ) -> TectonicResponseGradientSample:
        """Evaluate per-pair relief and its analytic Cartesian gradient."""
        source = context.sample
        weights = None if ridge_weights is None else ridge_weights.values
        relief = self.sample_from_context(source, ridge_weights=weights)
        count = len(source.plane_distance)
        zero = np.zeros((count, 3), dtype=np.float64)
        plane_grad = context.plane_distance_gradients
        distance = np.abs(source.plane_distance)
        distance_grad = np.sign(source.plane_distance)[:, None] * plane_grad
        conv_grad = context.convergence_gradients
        div_grad = context.divergence_gradients
        shear_grad = context.shear_gradients
        influence_grad = context.influence_gradients
        continental_grad = context.continental_blend_gradients
        polarity_grad = context.b_overrides_weight_gradients
        weight_grad = zero if ridge_weights is None else ridge_weights.gradients

        convergent_grad = np.zeros_like(zero)
        for i in range(count):
            collision_config = self.config.collision
            broad, crest, broad_d, crest_d = collision_profile_with_partials(
                distance[i],
                collision_config.width_fraction,
                self.config.collision_crest_width_fraction,
            )
            crest_height = 2.0
            base_shape = broad + crest_height * crest
            shape_d = broad_d + crest_height * crest_d
            ridge_blend = self.ridge_detail.config.blend if self.ridge_detail else 0.0
            if weights is not None and ridge_blend != 0.0:
                shape = (1.0 - ridge_blend) * base_shape + ridge_blend * broad * (
                    1.0 + 2.0 * weights[i]
                )
                shape_d = (1.0 - ridge_blend) * shape_d + ridge_blend * broad_d * (
                    1.0 + 2.0 * weights[i]
                )
                shape_grad = (
                    shape_d * distance_grad[i]
                    + ridge_blend * broad * 2.0 * weight_grad[i]
                )
            else:
                shape = base_shape
                shape_grad = shape_d * distance_grad[i]
            collision = source.convergence[i] * collision_config.height_fraction * shape
            collision_grad = collision_config.height_fraction * (
                conv_grad[i] * shape + source.convergence[i] * shape_grad
            )
            influence = source.influence[i]
            collision_grad = collision_grad * influence + collision * influence_grad[i]
            collision *= influence

            sub_config = self.config.subduction
            detail_strength = (
                self.ridge_detail.config.arc_strength if self.ridge_detail else 0.0
            )
            pair_subduction = 0.0
            pair_subduction_grad = np.zeros(3, dtype=np.float64)
            for sign, polarity in (
                (1.0, source.b_overrides_weight[i]),
                (-1.0, 1.0 - source.b_overrides_weight[i]),
            ):
                signed_distance = sign * source.plane_distance[i]
                if weights is not None and detail_strength != 0.0:
                    arc_variation = 1.0 + detail_strength * (2.0 * weights[i] - 1.0)
                else:
                    arc_variation = 1.0
                profile, profile_d, _, profile_arc_d = subduction_profile_with_partials(
                    signed_distance,
                    sub_config.width_fraction,
                    arc_height_multiplier=self.config.subduction_arc_height_multiplier,
                    arc_variation=arc_variation,
                    trench_depth_multiplier=self.config.subduction_trench_depth_multiplier,
                )
                profile_grad = profile_d * sign * plane_grad[i]
                if weights is not None and detail_strength != 0.0:
                    profile_grad += (
                        profile_arc_d * detail_strength * 2.0 * weight_grad[i]
                    )
                oriented = profile * source.convergence[i] * sub_config.height_fraction
                oriented_grad = sub_config.height_fraction * (
                    profile_grad * source.convergence[i] + profile * conv_grad[i]
                )
                pair_subduction += polarity * oriented
                if sign > 0.0:
                    polarity_derivative = polarity_grad[i]
                else:
                    polarity_derivative = -polarity_grad[i]
                pair_subduction_grad += (
                    polarity * oriented_grad + oriented * polarity_derivative
                )
            pair_subduction_grad = (
                pair_subduction_grad * influence + pair_subduction * influence_grad[i]
            )
            pair_subduction *= influence
            blend = source.continental_blend[i]
            convergent_grad[i] = (
                blend * collision_grad
                + (1.0 - blend) * pair_subduction_grad
                + (collision - pair_subduction) * continental_grad[i]
            )

        divergent_grad = np.zeros_like(zero)
        ridge_width = self.config.ridge.width_fraction
        rift_width = self.config.rift.width_fraction
        ridge_axial = self.config.ridge_axial_width_fraction
        ridge_strength = (
            self.ridge_detail.config.ridge_strength if self.ridge_detail else 0.0
        )
        rift_strength = (
            self.ridge_detail.config.rift_strength if self.ridge_detail else 0.0
        )
        for i in range(count):
            continental, continental_d = divergent_profile_with_partials(
                distance[i], rift_width, True
            )
            shoulders, shoulders_d = divergent_profile_with_partials(
                distance[i], rift_width, True, axial_depth_multiplier=0.0
            )
            signed_detail = 0.0 if weights is None else 2.0 * weights[i] - 1.0
            continental_detail = continental + rift_strength * shoulders * signed_detail
            continental_detail_d = (
                continental_d + rift_strength * shoulders_d * signed_detail
            )
            continental_detail_grad = continental_detail_d * distance_grad[i]
            if weights is not None:
                continental_detail_grad += (
                    rift_strength * shoulders * 2.0 * weight_grad[i]
                )
            continental_shape = continental_detail
            continental_detail *= (
                source.divergence[i] * self.config.rift.height_fraction
            )
            continental_detail_grad = self.config.rift.height_fraction * (
                continental_detail_grad * source.divergence[i]
                + continental_shape * div_grad[i]
            )

            oceanic, oceanic_d = divergent_profile_with_partials(
                distance[i],
                ridge_width,
                False,
                axial_width_fraction=ridge_axial,
            )
            axial_width = ridge_width * ridge_axial
            outer_position = (distance[i] - axial_width) / axial_width
            if outer_position <= 0.0:
                outer, outer_d = 0.0, 0.0
            elif outer_position >= 1.0:
                outer, outer_d = 1.0, 0.0
            else:
                outer = outer_position * outer_position * (3.0 - 2.0 * outer_position)
                outer_d = 6.0 * outer_position * (1.0 - outer_position) / axial_width
            oceanic_scale = 1.0 + ridge_strength * outer * signed_detail
            oceanic_detail = oceanic * oceanic_scale
            oceanic_detail_grad = (
                oceanic_d * oceanic_scale
                + oceanic * ridge_strength * outer_d * signed_detail
            ) * distance_grad[i]
            if weights is not None:
                oceanic_detail_grad += (
                    oceanic * ridge_strength * outer * 2.0 * weight_grad[i]
                )
            oceanic_shape = oceanic_detail
            oceanic_detail *= source.divergence[i] * self.config.ridge.height_fraction
            oceanic_detail_grad = self.config.ridge.height_fraction * (
                oceanic_detail_grad * source.divergence[i] + oceanic_shape * div_grad[i]
            )
            blend = source.continental_blend[i]
            mixed = blend * continental_detail + (1.0 - blend) * oceanic_detail
            mixed_grad = (
                blend * continental_detail_grad
                + (1.0 - blend) * oceanic_detail_grad
                + (continental_detail - oceanic_detail) * continental_grad[i]
            )
            divergent_grad[i] = (
                mixed_grad * source.influence[i] + mixed * influence_grad[i]
            )

        closing = source.convergence - source.divergence
        closing_grad = conv_grad - div_grad
        transform_grad = np.zeros_like(zero)
        shear_relief_grad = np.zeros_like(zero)
        smoothing = self.config.motion_smoothing_width
        for i in range(count):
            root = np.sqrt(closing[i] * closing[i] + smoothing * smoothing)
            denominator = root + source.shear[i]
            transform_motion_grad = (
                source.shear[i]
                / denominator
                * (1.0 - closing[i] * closing[i] / (root * denominator))
                * closing_grad[i]
                + closing[i]
                / denominator
                * (1.0 - source.shear[i] / denominator)
                * shear_grad[i]
            )
            shear_motion_grad = (
                -(source.shear[i] ** 2)
                * closing[i]
                / (root * denominator * denominator)
                * closing_grad[i]
                + (
                    2.0 * source.shear[i] / denominator
                    - source.shear[i] ** 2 / (denominator * denominator)
                )
                * shear_grad[i]
            )
            for is_transform, relief_config, motion_grad in (
                (True, self.config.transform, transform_motion_grad),
                (False, self.config.shear, shear_motion_grad),
            ):
                prof, prof_d, _ = transform_profile_with_partials(
                    distance[i], relief_config.width_fraction
                )
                detail_strength = (
                    self.ridge_detail.config.transform_strength
                    if is_transform and self.ridge_detail
                    else self.ridge_detail.config.shear_strength
                    if self.ridge_detail
                    else 0.0
                )
                factor = (
                    1.0
                    if weights is None
                    else 1.0 + detail_strength * (2.0 * weights[i] - 1.0)
                )
                factor_grad = (
                    np.zeros(3)
                    if weights is None
                    else detail_strength * 2.0 * weight_grad[i]
                )
                motion = (
                    (closing[i] if is_transform else source.shear[i])
                    * source.shear[i]
                    / denominator
                )
                height = relief_config.height_fraction
                base = prof * motion * factor * height
                gradient = (
                    height
                    * factor
                    * (prof_d * distance_grad[i] * motion + prof * motion_grad)
                    + prof * motion * height * factor_grad
                )
                gradient = gradient * source.influence[i] + base * influence_grad[i]
                if is_transform:
                    transform_grad[i] = gradient
                else:
                    shear_relief_grad[i] = gradient

        total_grad = (
            (convergent_grad + divergent_grad) + transform_grad
        ) + shear_relief_grad
        return TectonicResponseGradientSample(
            convergent=ScalarSample(relief.convergent, convergent_grad),
            divergent=ScalarSample(relief.divergent, divergent_grad),
            transform=ScalarSample(relief.transform, transform_grad),
            shear=ScalarSample(relief.shear, shear_relief_grad),
            total=ScalarSample(relief.total, total_grad),
        )

    def sample_with_gradient(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample:
        """Return summed tectonic relief and its analytic Cartesian gradient."""
        context = self.sample_context_with_gradient(positions, motion)
        ridge_weights = (
            self.ridge_detail.sample_with_gradient(positions)
            if self.ridge_detail is not None
            else None
        )
        if ridge_weights is not None:
            rows = motion.sample.query_indices
            ridge_weights = ScalarSample(
                ridge_weights.values[rows], ridge_weights.gradients[rows]
            )
        return self.sample_from_context_with_gradient(
            context, ridge_weights=ridge_weights
        ).total

    def sample_convergent_with_gradient(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample:
        """Return convergent relief and its analytic Cartesian gradient."""
        context = self.sample_context_with_gradient(positions, motion)
        ridge_weights = self._gradient_detail_weights(positions, motion)
        return self.sample_from_context_with_gradient(
            context, ridge_weights=ridge_weights
        ).convergent

    def sample_divergent_with_gradient(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample:
        """Return divergent relief and its analytic Cartesian gradient."""
        context = self.sample_context_with_gradient(positions, motion)
        return self.sample_from_context_with_gradient(
            context, ridge_weights=self._gradient_detail_weights(positions, motion)
        ).divergent

    def sample_transform_with_gradient(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample:
        """Return transform relief and its analytic Cartesian gradient."""
        context = self.sample_context_with_gradient(positions, motion)
        return self.sample_from_context_with_gradient(
            context, ridge_weights=self._gradient_detail_weights(positions, motion)
        ).transform

    def sample_shear_with_gradient(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample:
        """Return shear relief and its analytic Cartesian gradient."""
        context = self.sample_context_with_gradient(positions, motion)
        return self.sample_from_context_with_gradient(
            context, ridge_weights=self._gradient_detail_weights(positions, motion)
        ).shear

    def _gradient_detail_weights(
        self, positions: np.ndarray, motion: BoundaryMotionGradientSample
    ) -> ScalarSample | None:
        if self.ridge_detail is None:
            return None
        sample = self.ridge_detail.sample_with_gradient(positions)
        rows = motion.sample.query_indices
        return ScalarSample(sample.values[rows], sample.gradients[rows])

    def __call__(
        self, positions: np.ndarray, motion: BoundaryMotionSample
    ) -> np.ndarray:
        """Return the additive response across all four tectonic profiles."""
        context = self.sample_context(positions, motion)
        ridge_weights = (
            self.ridge_detail.sample(positions)[motion.query_indices]
            if self.ridge_detail is not None
            else None
        )
        return self.sample_from_context(context, ridge_weights=ridge_weights).total
