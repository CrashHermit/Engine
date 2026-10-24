"""Compose source-space tectonic relief from interpreted boundary context.

The raw relief profiles retain local shape falloff without pair weighting.
This module applies overlap influence once before the generic pair reduction.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from src.worldgen.relief.profile_config import ReliefProfileConfig

from src.worldgen.field.boundary_motion import (
    BoundaryMotionGradientSample,
    BoundaryMotionSample,
)
from src.worldgen.field.differential import ScalarSample
from src.worldgen.relief.collision import (
    collision_response_with_gradient,
    collision_relief,
)
from src.worldgen.relief.divergence import (
    continental_rift_relief,
    divergent_responses_with_gradient,
    oceanic_ridge_relief,
    ridge_flank_weight,
)
from src.worldgen.relief.fault import (
    fault_responses_with_gradient,
    fault_relief,
    shear_strength,
    transform_strength,
)
from src.worldgen.relief.ridge_detail import RidgeDetailField
from src.worldgen.relief.subduction import (
    subduction_response_with_gradient,
    subduction_relief,
)
from src.worldgen.geology.tectonic_context import (
    TectonicContextGradientSample,
    TectonicContextSample,
)
from src.worldgen.utilities.curves import saturating_response


@dataclass(frozen=True, slots=True)
class TectonicResponseConfig:
    """Tectonic spatial/height percentages and independent motion-response smoothing."""

    # Preserve narrow features while spreading the broad collision/ridge flanks.
    collision_crest_width_fraction: float = 0.2
    ridge_axial_width_fraction: float = 0.125
    # Calibrated independently of trench depth at Earth-reference scale.
    subduction_arc_height_multiplier: float = 1.05
    # Scales the trench independently from convergence and arc uplift.
    subduction_trench_depth_multiplier: float = 0.5
    # Positive regularization scale in motion units, not a spatial percentage.
    motion_smoothing_width: float = 0.01
    # Motion-amplitude saturation scale; expressed in motion units.
    motion_response_scale: float = 1.0

    collision: ReliefProfileConfig = field(
        default_factory=lambda: ReliefProfileConfig(
            width_percent=18.0, height_percent=0.03534
        )
    )
    subduction: ReliefProfileConfig = field(
        default_factory=lambda: ReliefProfileConfig(height_percent=0.0942)
    )
    rift: ReliefProfileConfig = field(
        default_factory=lambda: ReliefProfileConfig(height_percent=0.0314)
    )
    ridge: ReliefProfileConfig = field(
        default_factory=lambda: ReliefProfileConfig(
            width_percent=24.0, height_percent=0.03534
        )
    )
    transform: ReliefProfileConfig = field(
        default_factory=lambda: ReliefProfileConfig(
            width_percent=3.6, height_percent=0.00785
        )
    )
    shear: ReliefProfileConfig = field(
        default_factory=lambda: ReliefProfileConfig(
            width_percent=3.6, height_percent=0.00392
        )
    )


def blend_subduction_orientations(
    plane_distance: np.ndarray,
    convergence: np.ndarray,
    b_overrides_weight: np.ndarray,
    influence: np.ndarray,
    *,
    config: ReliefProfileConfig,
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
    convergence = saturating_response(convergence, scale=config.motion_response_scale)
    collision_values = (
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
        broad_values = (
            collision_relief(
                np.abs(plane_distance),
                convergence,
                config.collision.width_fraction,
                config.collision.height_fraction,
                crest_height_multiplier=0.0,
            )
            * influence
        )
        collision_values = (
            1.0 - ridge_blend
        ) * collision_values + ridge_blend * broad_values * (1.0 + 2.0 * ridge_weights)
    subduction_values = blend_subduction_orientations(
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
        continental_blend * collision_values
        + (1.0 - continental_blend) * subduction_values
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
    divergence = saturating_response(divergence, scale=config.motion_response_scale)
    distance = np.abs(plane_distance)
    rift_values = continental_rift_relief(
        distance,
        divergence,
        config.rift.width_fraction,
        config.rift.height_fraction,
    )
    ridge_values = oceanic_ridge_relief(
        distance,
        divergence,
        config.ridge.width_fraction,
        config.ridge.height_fraction,
        axial_width_fraction=config.ridge_axial_width_fraction,
    )
    if detail_weights is not None:
        signed_detail = 2.0 * detail_weights - 1.0
        # Isolate positive rift shoulders; axial subsidence is untouched.
        shoulder_values = continental_rift_relief(
            distance,
            divergence,
            config.rift.width_fraction,
            config.rift.height_fraction,
            axial_depth_multiplier=0.0,
        )
        rift_values = (
            rift_values + rift_detail_strength * shoulder_values * signed_detail
        )
        # Preserve the full axial feature; vary only the outer ridge flanks.
        axial_width = config.ridge.width_fraction * config.ridge_axial_width_fraction
        outer = ridge_flank_weight(distance, axial_width)
        ridge_values = ridge_values * (
            1.0 + ridge_detail_strength * outer * signed_detail
        )
    return (
        continental_blend * rift_values + (1.0 - continental_blend) * ridge_values
    ) * influence


def transform_boundary_relief(
    plane_distance: np.ndarray,
    closing: np.ndarray,
    shear: np.ndarray,
    influence: np.ndarray,
    *,
    smoothing: float,
    response_scale: float,
    config: ReliefProfileConfig = ReliefProfileConfig(
        width_percent=3.6, height_percent=0.00785
    ),
    detail_weights: np.ndarray | None = None,
    detail_strength: float = 0.0,
) -> np.ndarray:
    """Return compact oblique transform uplift or subsidence at boundary pairs."""
    strength = saturating_response(
        transform_strength(closing, shear, smoothing=smoothing), scale=response_scale
    )
    if detail_weights is not None:
        strength = strength * (1.0 + detail_strength * (2.0 * detail_weights - 1.0))
    return (
        fault_relief(
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
    response_scale: float,
    config: ReliefProfileConfig = ReliefProfileConfig(
        width_percent=3.6, height_percent=0.00392
    ),
    detail_weights: np.ndarray | None = None,
    detail_strength: float = 0.0,
) -> np.ndarray:
    """Return compact residual pure-shear relief at boundary pairs."""
    strength = saturating_response(
        shear_strength(closing, shear, smoothing=smoothing), scale=response_scale
    )
    if detail_weights is not None:
        strength = strength * (1.0 + detail_strength * (2.0 * detail_weights - 1.0))
    return (
        fault_relief(
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
class TectonicReliefGradientSample:
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
    sample_context_with_gradient: Callable[
        [np.ndarray, BoundaryMotionGradientSample], TectonicContextGradientSample
    ] = field(kw_only=True)

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
            response_scale=self.config.motion_response_scale,
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
            response_scale=self.config.motion_response_scale,
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
            response_scale=self.config.motion_response_scale,
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
            response_scale=self.config.motion_response_scale,
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
    ) -> TectonicReliefGradientSample:
        source = context.sample
        detail_weights = None if ridge_weights is None else ridge_weights.values
        if ridge_weights is None:
            detail_weights = np.empty(0, dtype=np.float64)
            detail_weight_gradients = np.empty((0, 3), dtype=np.float64)
        else:
            detail_weight_gradients = ridge_weights.gradients
        detail = None if self.ridge_detail is None else self.ridge_detail.config
        config = self.config
        collision, collision_gradients, collision_values = (
            collision_response_with_gradient(
                source.plane_distance,
                source.convergence,
                source.influence,
                context.plane_distance_gradients,
                context.convergence_gradients,
                detail_weights,
                detail_weight_gradients,
                (
                    config.collision.width_fraction,
                    config.collision.height_fraction,
                    config.collision_crest_width_fraction,
                ),
                config.motion_response_scale,
                0.0 if detail is None else detail.blend,
            )
        )
        subduction, subduction_gradients = subduction_response_with_gradient(
            source.plane_distance,
            source.convergence,
            source.b_overrides_weight,
            context.plane_distance_gradients,
            context.convergence_gradients,
            context.b_overrides_weight_gradients,
            detail_weights,
            detail_weight_gradients,
            (
                config.subduction.width_fraction,
                config.subduction.height_fraction,
                config.subduction_arc_height_multiplier,
                config.subduction_trench_depth_multiplier,
            ),
            config.motion_response_scale,
            0.0 if detail is None else detail.arc_strength,
        )
        influence = source.influence[:, None]
        influence_gradients = context.influence_gradients
        continental_blend = source.continental_blend[:, None]
        continental_blend_gradients = context.continental_blend_gradients
        collision_gradients = (
            collision_gradients * influence + collision[:, None] * influence_gradients
        )
        subduction_gradients = (
            subduction_gradients * influence + subduction[:, None] * influence_gradients
        )
        convergent_gradients = (
            continental_blend * collision_gradients
            + (1.0 - continental_blend) * subduction_gradients
            + (collision * source.influence - subduction * source.influence)[:, None]
            * continental_blend_gradients
        )
        rift, rift_gradients, ridge, ridge_gradients = (
            divergent_responses_with_gradient(
                source.plane_distance,
                source.divergence,
                context.plane_distance_gradients,
                context.divergence_gradients,
                detail_weights,
                detail_weight_gradients,
                (config.rift.width_fraction, config.rift.height_fraction),
                (
                    config.ridge.width_fraction,
                    config.ridge.height_fraction,
                    config.ridge_axial_width_fraction,
                ),
                config.motion_response_scale,
                0.0 if detail is None else detail.rift_strength,
                0.0 if detail is None else detail.ridge_strength,
            )
        )
        divergent_values = (
            source.continental_blend * rift + (1.0 - source.continental_blend) * ridge
        )
        divergent_gradients = (
            continental_blend * rift_gradients
            + (1.0 - continental_blend) * ridge_gradients
            + (rift - ridge)[:, None] * continental_blend_gradients
        )
        divergent_gradients = (
            divergent_gradients * influence
            + divergent_values[:, None] * influence_gradients
        )
        transform, transform_gradients, shear, shear_relief_gradients = (
            fault_responses_with_gradient(
                source.plane_distance,
                source.convergence - source.divergence,
                source.shear,
                context.plane_distance_gradients,
                context.convergence_gradients - context.divergence_gradients,
                context.shear_gradients,
                detail_weights,
                detail_weight_gradients,
                (
                    config.transform.width_fraction,
                    config.transform.height_fraction,
                    0.0 if detail is None else detail.transform_strength,
                ),
                (
                    config.shear.width_fraction,
                    config.shear.height_fraction,
                    0.0 if detail is None else detail.shear_strength,
                ),
                config.motion_smoothing_width,
                config.motion_response_scale,
            )
        )
        transform_gradients = (
            transform_gradients * influence + transform[:, None] * influence_gradients
        )
        shear_relief_gradients = (
            shear_relief_gradients * influence + shear[:, None] * influence_gradients
        )
        convergent_values = source.continental_blend * collision_values + (
            1.0 - source.continental_blend
        ) * (subduction * source.influence)
        divergent_values = (
            source.continental_blend * rift + (1.0 - source.continental_blend) * ridge
        ) * source.influence
        transform_values = transform * source.influence
        shear_values = shear * source.influence
        total_values = (
            (convergent_values + divergent_values) + transform_values
        ) + shear_values
        for values in (
            convergent_values,
            divergent_values,
            transform_values,
            shear_values,
            total_values,
        ):
            values.setflags(write=False)

        total_gradients = (
            (convergent_gradients + divergent_gradients) + transform_gradients
        ) + shear_relief_gradients
        return TectonicReliefGradientSample(
            convergent=ScalarSample(convergent_values, convergent_gradients),
            divergent=ScalarSample(divergent_values, divergent_gradients),
            transform=ScalarSample(transform_values, transform_gradients),
            shear=ScalarSample(shear_values, shear_relief_gradients),
            total=ScalarSample(total_values, total_gradients),
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
