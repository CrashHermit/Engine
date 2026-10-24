"""Collision relief profiles and their compiled per-pair evaluators."""

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
def collision_profile_with_partials(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float, float, float]:
    """Return broad/crest profiles and their distance derivatives."""
    if width <= 0.0:
        return 0.0, 0.0, 0.0, 0.0
    broad = smoothstep_scalar(1.0 - distance / width)
    crest_input = distance / (width * crest_width_fraction)
    crest_complement = 1.0 - smoothstep_scalar(crest_input)
    crest = crest_complement * crest_complement
    broad_derivative = -smoothstep_derivative_scalar(1.0 - distance / width) / width
    crest_derivative = (
        -2.0
        * crest_complement
        * smoothstep_derivative_scalar(crest_input)
        / (width * crest_width_fraction)
    )
    return broad, crest, broad_derivative, crest_derivative


@register_jitable
def collision_profile(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float]:
    """Return normalized broad mountain response and squared crest weight."""
    broad = smoothstep_scalar(1.0 - distance / width)
    crest_weight = 1.0 - smoothstep_scalar(distance / (width * crest_width_fraction))
    return broad, crest_weight**2


@register_jitable
def collision_value(distance, parameters, peak):
    """Evaluate broad uplift and a narrow crest without temporary arrays."""
    width, height, crest_width, crest_height = parameters
    if distance >= width:
        return 0.0
    broad, crest = collision_profile(distance, width, crest_width)
    return peak * (broad + crest_height * crest) * height


@njit(cache=True)
def collision_relief(
    distances: np.ndarray,
    convergence: np.ndarray,
    width: float,
    height: float,
    crest_width_fraction: float = 0.3,
    crest_height_multiplier: float = 2.0,
) -> np.ndarray:
    """Broad collision uplift with an independently weighted narrow crest."""
    result = np.empty(len(distances), dtype=np.float64)
    parameters = (width, height, crest_width_fraction, crest_height_multiplier)
    for i in range(len(distances)):
        result[i] = collision_value(distances[i], parameters, convergence[i])
    return result


@register_jitable(inline="always")
def _collision_response_with_gradient(
    plane_distance: np.ndarray,
    convergence_values: np.ndarray,
    influence_values: np.ndarray,
    plane_distance_gradients: np.ndarray,
    convergence_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    parameters: tuple[float, float, float],
    response_scale: float,
    ridge_blend: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Differentiate the collision response before material and overlap blending."""
    width, height, crest_width = parameters
    count = len(plane_distance)
    values = np.empty(count, dtype=np.float64)
    weighted_values = np.empty(count, dtype=np.float64)
    gradients = np.empty((count, 3), dtype=np.float64)
    for i in prange(count):
        broad, crest, broad_d, crest_d = collision_profile_with_partials(
            abs(plane_distance[i]), width, crest_width
        )
        base_shape = broad + 2.0 * crest
        shape_d = broad_d + 2.0 * crest_d
        if len(detail_weights) != 0 and ridge_blend != 0.0:
            shape_d = (1.0 - ridge_blend) * shape_d + ridge_blend * broad_d * (
                1.0 + 2.0 * detail_weights[i]
            )
        convergence = saturating_response(convergence_values[i], scale=response_scale)
        chain = saturating_response_derivative(
            convergence_values[i], scale=response_scale
        )
        shape = base_shape
        if len(detail_weights) != 0 and ridge_blend != 0.0:
            shape = (1.0 - ridge_blend) * shape + ridge_blend * broad * (
                1.0 + 2.0 * detail_weights[i]
            )
        values[i] = convergence * shape * height
        base_value = convergence * base_shape * height
        weighted_base = base_value * influence_values[i]
        if len(detail_weights) != 0 and ridge_blend != 0.0:
            broad_value = convergence * broad * height
            weighted_broad = broad_value * influence_values[i]
            weighted_values[i] = (
                1.0 - ridge_blend
            ) * weighted_base + ridge_blend * weighted_broad * (
                1.0 + 2.0 * detail_weights[i]
            )
        else:
            weighted_values[i] = weighted_base
        for axis in range(3):
            shape_gradient = shape_d * (
                np.sign(plane_distance[i]) * plane_distance_gradients[i, axis]
            )
            if len(detail_weights) != 0 and ridge_blend != 0.0:
                shape_gradient += (
                    ridge_blend * broad * 2.0 * detail_weight_gradients[i, axis]
                )
            gradients[i, axis] = height * (
                convergence_gradients[i, axis] * chain * shape
                + convergence * shape_gradient
            )
    return values, gradients, weighted_values


_collision_response_serial = njit(cache=True)(_collision_response_with_gradient)


@njit(cache=True, parallel=True)
def _collision_response_parallel(
    plane_distance: np.ndarray,
    convergence_values: np.ndarray,
    influence_values: np.ndarray,
    plane_distance_gradients: np.ndarray,
    convergence_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    parameters: tuple[float, float, float],
    response_scale: float,
    ridge_blend: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return _collision_response_with_gradient(
        plane_distance,
        convergence_values,
        influence_values,
        plane_distance_gradients,
        convergence_gradients,
        detail_weights,
        detail_weight_gradients,
        parameters,
        response_scale,
        ridge_blend,
    )


def collision_response_with_gradient(
    plane_distance: np.ndarray,
    convergence_values: np.ndarray,
    influence_values: np.ndarray,
    plane_distance_gradients: np.ndarray,
    convergence_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    parameters: tuple[float, float, float],
    response_scale: float,
    ridge_blend: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate motion-modulated collision relief and its Cartesian gradient.

    Parameters are width, height, and crest-width fraction. Empty detail
    weights disable ridge detail. Material mixing and overlap are not applied.
    """
    kernel = _collision_response_serial
    if len(plane_distance) >= 1024:
        kernel = _collision_response_parallel
    return kernel(
        plane_distance,
        convergence_values,
        influence_values,
        plane_distance_gradients,
        convergence_gradients,
        detail_weights,
        detail_weight_gradients,
        parameters,
        response_scale,
        ridge_blend,
    )
