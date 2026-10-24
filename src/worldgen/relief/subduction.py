"""Signed trench and overriding-arc profiles and compiled evaluators."""

import numpy as np
from numba import njit, prange
from numba.extending import register_jitable

from src.worldgen.utilities.curves import (
    saturating_response,
    saturating_response_derivative,
    smoothstep_derivative_scalar,
    smoothstep_scalar,
)


@register_jitable
def subduction_profile(
    signed_distance: float,
    width: float,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    arc_variation: float = 1.0,
    trench_depth_multiplier: float = 1.0,
) -> float:
    """Return continuous relief: negative distance descends, positive overrides.

    The trench depth and overriding arc amplitude are independently scaled.
    """
    if width <= 0.0:
        return 0.0
    trench = -trench_depth_multiplier * smoothstep_scalar(
        1.0 - abs(signed_distance) / (width * trench_width_fraction)
    )
    if signed_distance <= 0.0:
        return trench
    arc_position = signed_distance / width
    arc_input = 1.0 - abs(arc_position - arc_offset_fraction) / arc_width_fraction
    # Keep volcanic uplift zero at the trench even if its support overlaps zero.
    forearc_rise = smoothstep_scalar(arc_position / arc_offset_fraction)
    arc = arc_height_multiplier * smoothstep_scalar(arc_input) * forearc_rise
    return trench + arc * arc_variation


@register_jitable
def subduction_profile_with_partials(
    signed_distance: float,
    width: float,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    arc_variation: float = 1.0,
    trench_depth_multiplier: float = 1.0,
) -> tuple[float, float, float, float]:
    """Return relief and partials by signed distance, width, and arc variation."""
    value = subduction_profile(
        signed_distance,
        width,
        trench_width_fraction,
        arc_offset_fraction,
        arc_width_fraction,
        arc_height_multiplier,
        arc_variation,
        trench_depth_multiplier,
    )
    if width <= 0.0:
        return value, 0.0, 0.0, 0.0
    trench_scale = width * trench_width_fraction
    trench_input = 1.0 - abs(signed_distance) / trench_scale
    trench_slope = smoothstep_derivative_scalar(trench_input)
    trench_d_distance = (
        trench_depth_multiplier
        * trench_slope
        * (1.0 if signed_distance > 0.0 else -1.0)
        / trench_scale
    )
    trench_d_width = (
        -trench_depth_multiplier
        * trench_slope
        * abs(signed_distance)
        / (width * width * trench_width_fraction)
    )
    if signed_distance <= 0.0:
        return value, trench_d_distance, trench_d_width, 0.0
    arc_position = signed_distance / width
    arc_input = 1.0 - abs(arc_position - arc_offset_fraction) / arc_width_fraction
    arc_abs_sign = 1.0 if arc_position > arc_offset_fraction else -1.0
    arc_profile = smoothstep_scalar(arc_input)
    arc_profile_d_position = (
        -smoothstep_derivative_scalar(arc_input) * arc_abs_sign / arc_width_fraction
    )
    forearc_input = arc_position / arc_offset_fraction
    forearc = smoothstep_scalar(forearc_input)
    forearc_d_position = (
        smoothstep_derivative_scalar(forearc_input) / arc_offset_fraction
    )
    arc_product = arc_profile * forearc
    arc_d_position = arc_profile_d_position * forearc + arc_profile * forearc_d_position
    arc_scale = arc_height_multiplier * arc_variation
    return (
        value,
        trench_d_distance + arc_scale * arc_d_position / width,
        trench_d_width - arc_scale * arc_d_position * arc_position / width,
        arc_height_multiplier * arc_product,
    )


@register_jitable
def subduction_value(signed_distance, parameters, peak, arc_variation):
    """Evaluate the existing finite-support trench/arc response."""
    width, height, trench_width, arc_offset, arc_width, arc_height, trench_depth = (
        parameters
    )
    if abs(signed_distance) >= width:
        return 0.0
    profile = subduction_profile(
        signed_distance,
        width,
        trench_width,
        arc_offset,
        arc_width,
        arc_height,
        arc_variation,
        trench_depth,
    )
    return profile * peak * height


@njit(cache=True)
def subduction_relief(
    signed_distances: np.ndarray,
    convergence: np.ndarray,
    width: float,
    height: float,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    trench_depth_multiplier: float = 1.0,
) -> np.ndarray:
    """Trench at zero and arc on the positive (overriding) side.

    The consumer supplies polarity: negative is the descending side. These
    are signed source-face distances, not distances signed by motion direction.
    """
    result = np.empty(len(signed_distances), dtype=np.float64)
    parameters = (
        width,
        height,
        trench_width_fraction,
        arc_offset_fraction,
        arc_width_fraction,
        arc_height_multiplier,
        trench_depth_multiplier,
    )
    for i in range(len(signed_distances)):
        result[i] = subduction_value(
            signed_distances[i], parameters, convergence[i], 1.0
        )
    return result


@register_jitable(inline="always")
def _subduction_response_with_gradient(
    plane_distance: np.ndarray,
    convergence_values: np.ndarray,
    b_overrides_weight: np.ndarray,
    plane_distance_gradients: np.ndarray,
    convergence_gradients: np.ndarray,
    b_overrides_weight_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    parameters: tuple[float, float, float, float],
    response_scale: float,
    arc_strength: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Differentiate both ordered subduction orientations without pair overlap."""
    width, height, arc_height, trench_depth = parameters
    count = len(plane_distance)
    values = np.empty(count, dtype=np.float64)
    gradients = np.empty((count, 3), dtype=np.float64)
    for i in prange(count):
        convergence = saturating_response(convergence_values[i], scale=response_scale)
        chain = saturating_response_derivative(
            convergence_values[i], scale=response_scale
        )
        value = 0.0
        dx = 0.0
        dy = 0.0
        dz = 0.0
        for sign, overriding in (
            (1.0, b_overrides_weight[i]),
            (-1.0, 1.0 - b_overrides_weight[i]),
        ):
            arc_variation = 1.0
            has_detail = len(detail_weights) != 0 and arc_strength != 0.0
            if has_detail:
                arc_variation = 1.0 + arc_strength * (2.0 * detail_weights[i] - 1.0)
            profile, profile_d, _, profile_arc_d = subduction_profile_with_partials(
                sign * plane_distance[i],
                width,
                arc_height_multiplier=arc_height,
                arc_variation=arc_variation,
                trench_depth_multiplier=trench_depth,
            )
            oriented = profile * convergence * height
            if has_detail:
                base_profile = subduction_profile(
                    sign * plane_distance[i],
                    width,
                    arc_height_multiplier=arc_height,
                    trench_depth_multiplier=trench_depth,
                )
                base = base_profile * convergence * height
                trench_profile = subduction_profile(
                    sign * plane_distance[i],
                    width,
                    arc_height_multiplier=0.0,
                    trench_depth_multiplier=trench_depth,
                )
                trench = trench_profile * convergence * height
                oriented = trench + (base - trench) * arc_variation
            value += overriding * oriented
            for axis in range(3):
                profile_gradient = profile_d * sign * plane_distance_gradients[i, axis]
                if len(detail_weights) != 0 and arc_strength != 0.0:
                    profile_gradient += (
                        profile_arc_d
                        * arc_strength
                        * 2.0
                        * detail_weight_gradients[i, axis]
                    )
                oriented_gradient = height * (
                    profile_gradient * convergence
                    + profile * convergence_gradients[i, axis] * chain
                )
                polarity_derivative = b_overrides_weight_gradients[i, axis]
                if sign < 0.0:
                    polarity_derivative = -polarity_derivative
                contribution = (
                    overriding * oriented_gradient + oriented * polarity_derivative
                )
                if axis == 0:
                    dx += contribution
                elif axis == 1:
                    dy += contribution
                else:
                    dz += contribution
        values[i] = value
        gradients[i, 0] = dx
        gradients[i, 1] = dy
        gradients[i, 2] = dz
    return values, gradients


_subduction_response_serial = njit(cache=True)(_subduction_response_with_gradient)


@njit(cache=True, parallel=True)
def _subduction_response_parallel(
    plane_distance: np.ndarray,
    convergence_values: np.ndarray,
    b_overrides_weight: np.ndarray,
    plane_distance_gradients: np.ndarray,
    convergence_gradients: np.ndarray,
    b_overrides_weight_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    parameters: tuple[float, float, float, float],
    response_scale: float,
    arc_strength: float,
) -> tuple[np.ndarray, np.ndarray]:
    return _subduction_response_with_gradient(
        plane_distance,
        convergence_values,
        b_overrides_weight,
        plane_distance_gradients,
        convergence_gradients,
        b_overrides_weight_gradients,
        detail_weights,
        detail_weight_gradients,
        parameters,
        response_scale,
        arc_strength,
    )


def subduction_response_with_gradient(
    plane_distance: np.ndarray,
    convergence_values: np.ndarray,
    b_overrides_weight: np.ndarray,
    plane_distance_gradients: np.ndarray,
    convergence_gradients: np.ndarray,
    b_overrides_weight_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    parameters: tuple[float, float, float, float],
    response_scale: float,
    arc_strength: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate both subduction orientations and their blended gradient.

    Parameters are width, height, arc-height multiplier, and trench-depth
    multiplier. ``b_overrides_weight`` blends toward B at one and toward A
    at zero. Empty detail weights disable arc detail; material and overlap
    weighting are left to the consumer.
    """
    kernel = _subduction_response_serial
    if len(plane_distance) >= 1024:
        kernel = _subduction_response_parallel
    return kernel(
        plane_distance,
        convergence_values,
        b_overrides_weight,
        plane_distance_gradients,
        convergence_gradients,
        b_overrides_weight_gradients,
        detail_weights,
        detail_weight_gradients,
        parameters,
        response_scale,
        arc_strength,
    )
