"""Divergent ridge, rift, and flank profiles with compiled evaluators."""

import numpy as np
from numba import njit, prange
from numba.extending import register_jitable

from src.worldgen.utilities.curves import (
    clamp_unit,
    saturating_response,
    saturating_response_derivative,
    smoothstep,
    smoothstep_derivative_scalar,
    smoothstep_scalar,
)

_PARALLEL_GRADIENT_RECORDS = 1024


@register_jitable
def divergent_response(continental: bool) -> float:
    """Return the sign of divergent axial relief for a crust type."""
    return -1.0 if continental else 1.0


@register_jitable
def divergent_profile(
    distance: float,
    width: float,
    continental: bool,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
    shoulder_height_multiplier: float = 0.35,
) -> float:
    """Return normalized divergent relief at distance from its boundary."""
    if width <= 0.0:
        return 0.0
    t = clamp_unit(distance / width)
    broad_input = 1.0 - t
    axial_input = 1.0 - t / axial_width_fraction
    broad = smoothstep_scalar(broad_input)
    axial = smoothstep_scalar(axial_input)
    signed_axial = divergent_response(continental) * axial_depth_multiplier * axial
    if continental:
        shoulders = (
            shoulder_height_multiplier * 16.0 * t * t * (1.0 - t) * (1.0 - t) * broad
        )
        return shoulders + signed_axial
    return broad - signed_axial


@register_jitable
def divergent_profile_with_partials(
    distance: float,
    width: float,
    continental: bool,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
    shoulder_height_multiplier: float = 0.35,
) -> tuple[float, float]:
    """Return divergent relief and its distance derivative."""
    if width <= 0.0 or distance >= width:
        return 0.0, 0.0
    t = clamp_unit(distance / width)
    broad_input = 1.0 - t
    axial_input = 1.0 - t / axial_width_fraction
    broad = smoothstep_scalar(broad_input)
    axial = smoothstep_scalar(axial_input)
    broad_dt = -smoothstep_derivative_scalar(broad_input)
    axial_dt = -smoothstep_derivative_scalar(axial_input) / axial_width_fraction
    signed_axial = divergent_response(continental) * axial_depth_multiplier * axial
    signed_axial_dt = (
        divergent_response(continental) * axial_depth_multiplier * axial_dt
    )
    if continental:
        shoulder_base = 16.0 * t * t * (1.0 - t) * (1.0 - t)
        shoulder_dt = 32.0 * t * (1.0 - t) * (1.0 - 2.0 * t)
        derivative_t = (
            shoulder_height_multiplier
            * (shoulder_dt * broad + shoulder_base * broad_dt)
            + signed_axial_dt
        )
    else:
        derivative_t = broad_dt - signed_axial_dt
    value = divergent_profile(
        distance,
        width,
        continental,
        axial_width_fraction,
        axial_depth_multiplier,
        shoulder_height_multiplier,
    )
    return value, derivative_t / width


@register_jitable
def divergence_value(distance, parameters, peak, continental):
    """Evaluate the existing material-specific divergent response."""
    width, height, axial_width, axial_depth, shoulder_height = parameters
    if distance >= width:
        return 0.0
    profile = divergent_profile(
        distance, width, continental, axial_width, axial_depth, shoulder_height
    )
    return profile * peak * height


@njit(cache=True)
def continental_rift_relief(
    distances: np.ndarray,
    divergence: np.ndarray,
    width: float,
    height: float,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
    shoulder_height_multiplier: float = 0.35,
) -> np.ndarray:
    """Negative axial rift with positive flanking shoulders."""
    result = np.empty(len(distances), dtype=np.float64)
    parameters = (
        width,
        height,
        axial_width_fraction,
        axial_depth_multiplier,
        shoulder_height_multiplier,
    )
    for i in range(len(distances)):
        result[i] = divergence_value(distances[i], parameters, divergence[i], True)
    return result


@njit(cache=True)
def oceanic_ridge_relief(
    distances: np.ndarray,
    divergence: np.ndarray,
    width: float,
    height: float,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
) -> np.ndarray:
    """Broad positive ridge with a central axial depression, not a trench."""
    result = np.empty(len(distances), dtype=np.float64)
    parameters = (width, height, axial_width_fraction, axial_depth_multiplier, 0.0)
    for i in range(len(distances)):
        result[i] = divergence_value(distances[i], parameters, divergence[i], False)
    return result


def ridge_flank_weight(distance: np.ndarray, axial_width: float) -> np.ndarray:
    """Return the smooth outer-flank weight beyond the axial feature."""
    return smoothstep(np.clip((distance - axial_width) / axial_width, 0.0, 1.0))


@register_jitable
def ridge_flank_weight_with_partials(
    distance: float, axial_width: float
) -> tuple[float, float]:
    """Return the outer-flank weight and its distance derivative."""
    outer_position = (distance - axial_width) / axial_width
    if outer_position <= 0.0:
        return 0.0, 0.0
    if outer_position >= 1.0:
        return 1.0, 0.0
    value = outer_position * outer_position * (3.0 - 2.0 * outer_position)
    derivative = 6.0 * outer_position * (1.0 - outer_position) / axial_width

    return value, derivative


@register_jitable(inline="always")
def _divergent_responses_with_gradient(
    plane_distance: np.ndarray,
    divergence_values: np.ndarray,
    plane_distance_gradients: np.ndarray,
    divergence_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    rift_parameters: tuple[float, float],
    ridge_parameters: tuple[float, float, float],
    response_scale: float,
    rift_strength: float,
    ridge_strength: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rift_width, rift_height = rift_parameters
    ridge_width, ridge_height, ridge_axial = ridge_parameters
    count = len(plane_distance)
    rift_values = np.empty(count, dtype=np.float64)
    rift_gradients = np.empty((count, 3), dtype=np.float64)
    ridge_values = np.empty(count, dtype=np.float64)
    ridge_gradients = np.empty((count, 3), dtype=np.float64)
    for i in prange(count):
        distance = abs(plane_distance[i])
        distance_sign = np.sign(plane_distance[i])
        rift, rift_d = divergent_profile_with_partials(distance, rift_width, True)
        shoulders, shoulders_d = divergent_profile_with_partials(
            distance, rift_width, True, axial_depth_multiplier=0.0
        )
        signed_detail = (
            0.0 if len(detail_weights) == 0 else 2.0 * detail_weights[i] - 1.0
        )
        rift_shape = rift + rift_strength * shoulders * signed_detail
        rift_shape_d = rift_d + rift_strength * shoulders_d * signed_detail
        divergence = saturating_response(divergence_values[i], scale=response_scale)
        divergence_chain = saturating_response_derivative(
            divergence_values[i], scale=response_scale
        )
        ridge, ridge_d = divergent_profile_with_partials(
            distance, ridge_width, False, axial_width_fraction=ridge_axial
        )
        outer, outer_d = ridge_flank_weight_with_partials(
            distance, ridge_width * ridge_axial
        )
        ridge_scale = 1.0 + ridge_strength * outer * signed_detail
        ridge_shape = ridge * ridge_scale
        rift_base = rift * divergence * rift_height
        shoulders_base = shoulders * divergence * rift_height
        ridge_base = ridge * divergence * ridge_height
        rift_values[i] = rift_base + rift_strength * shoulders_base * signed_detail
        ridge_values[i] = ridge_base * ridge_scale
        for axis in range(3):
            distance_gradient = distance_sign * plane_distance_gradients[i, axis]
            rift_gradient = rift_shape_d * distance_gradient
            ridge_gradient = (
                ridge_d * ridge_scale + ridge * ridge_strength * outer_d * signed_detail
            ) * distance_gradient
            if len(detail_weights) != 0:
                rift_gradient += (
                    rift_strength * shoulders * 2.0 * detail_weight_gradients[i, axis]
                )
                ridge_gradient += (
                    ridge
                    * ridge_strength
                    * outer
                    * 2.0
                    * detail_weight_gradients[i, axis]
                )
            rift_gradients[i, axis] = rift_height * (
                rift_gradient * divergence
                + rift_shape * divergence_gradients[i, axis] * divergence_chain
            )
            ridge_gradients[i, axis] = ridge_height * (
                ridge_gradient * divergence
                + ridge_shape * divergence_gradients[i, axis] * divergence_chain
            )
    return rift_values, rift_gradients, ridge_values, ridge_gradients


_divergent_responses_serial = njit(cache=True)(_divergent_responses_with_gradient)


@njit(cache=True, parallel=True)
def _divergent_responses_parallel(
    plane_distance: np.ndarray,
    divergence_values: np.ndarray,
    plane_distance_gradients: np.ndarray,
    divergence_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    rift_parameters: tuple[float, float],
    ridge_parameters: tuple[float, float, float],
    response_scale: float,
    rift_strength: float,
    ridge_strength: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return _divergent_responses_with_gradient(
        plane_distance,
        divergence_values,
        plane_distance_gradients,
        divergence_gradients,
        detail_weights,
        detail_weight_gradients,
        rift_parameters,
        ridge_parameters,
        response_scale,
        rift_strength,
        ridge_strength,
    )


def divergent_responses_with_gradient(
    plane_distance: np.ndarray,
    divergence_values: np.ndarray,
    plane_distance_gradients: np.ndarray,
    divergence_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    rift_parameters: tuple[float, float],
    ridge_parameters: tuple[float, float, float],
    response_scale: float,
    rift_strength: float,
    ridge_strength: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return unweighted rift values/gradients, then ridge values/gradients.

    Motion saturation and detail are included; material mixing and overlap
    weighting are not. Empty detail weights disable procedural detail.
    """
    kernel = _divergent_responses_serial
    if len(plane_distance) >= _PARALLEL_GRADIENT_RECORDS:
        kernel = _divergent_responses_parallel
    return kernel(
        plane_distance,
        divergence_values,
        plane_distance_gradients,
        divergence_gradients,
        detail_weights,
        detail_weight_gradients,
        rift_parameters,
        ridge_parameters,
        response_scale,
        rift_strength,
        ridge_strength,
    )
