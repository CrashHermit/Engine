"""Shared compact fault attenuation and motion-response functions."""

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
def fault_profile(distance: float, width: float) -> float:
    """Return compact smoothstep attenuation across a fault-relief width."""
    if width <= 0.0:
        return 0.0
    return smoothstep_scalar(1.0 - distance / width)


@register_jitable
def fault_profile_with_partials(
    distance: float, width: float
) -> tuple[float, float, float]:
    """Return attenuation and partials with respect to distance and width."""
    value = fault_profile(distance, width)
    if width <= 0.0:
        return value, 0.0, 0.0
    argument = 1.0 - distance / width
    slope = smoothstep_derivative_scalar(argument)
    return value, -slope / width, slope * distance / (width * width)


def transform_strength(
    normal: np.ndarray | float, shear: np.ndarray | float, *, smoothing: float
) -> np.ndarray | float:
    """Return signed transform response with smoothed normal magnitude."""
    denominator = np.sqrt(normal * normal + smoothing * smoothing) + shear
    return normal * shear / denominator


@register_jitable
def transform_strength_with_partials(
    normal: np.ndarray | float, shear: np.ndarray | float, smoothing: float
) -> tuple[np.ndarray | float, np.ndarray | float, np.ndarray | float]:
    """Return transform response and partials by normal motion and shear."""
    root = np.sqrt(normal * normal + smoothing * smoothing)
    denominator = root + shear
    value = normal * shear / denominator
    d_normal = shear / denominator * (1.0 - normal * normal / (root * denominator))
    d_shear = normal / denominator * (1.0 - shear / denominator)
    return value, d_normal, d_shear


def shear_strength(
    normal: np.ndarray | float, shear: np.ndarray | float, *, smoothing: float
) -> np.ndarray | float:
    """Return nonnegative shear response with smoothed normal magnitude."""
    denominator = np.sqrt(normal * normal + smoothing * smoothing) + shear
    return shear * shear / denominator


@register_jitable
def shear_strength_with_partials(
    normal: np.ndarray | float, shear: np.ndarray | float, smoothing: float
) -> tuple[np.ndarray | float, np.ndarray | float, np.ndarray | float]:
    """Return shear response and partials by normal motion and shear."""
    root = np.sqrt(normal * normal + smoothing * smoothing)
    denominator = root + shear
    value = shear * shear / denominator
    d_normal = -(shear * shear) * normal / (root * denominator * denominator)
    d_shear = 2.0 * shear / denominator - shear * shear / (denominator * denominator)
    return value, d_normal, d_shear


@register_jitable
def fault_value(distance, parameters, peak):
    """Evaluate compact signed fault relief without temporary arrays."""
    width, height = parameters
    if distance >= width:
        return 0.0
    return fault_profile(distance, width) * peak * height


@njit(cache=True)
def fault_relief(
    distances: np.ndarray,
    strengths: np.ndarray,
    width: float,
    height: float,
) -> np.ndarray:
    """Evaluate compact fault relief for one signed or nonnegative strength."""
    result = np.empty(len(distances), dtype=np.float64)
    for i in range(len(distances)):
        result[i] = fault_value(distances[i], (width, height), strengths[i])
    return result


@register_jitable(inline="always")
def _fault_responses_with_gradient(
    plane_distance: np.ndarray,
    closing: np.ndarray,
    shear: np.ndarray,
    plane_distance_gradients: np.ndarray,
    closing_gradients: np.ndarray,
    shear_motion_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    transform_parameters: tuple[float, float, float],
    shear_parameters: tuple[float, float, float],
    smoothing: float,
    response_scale: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    count = len(plane_distance)
    transform_values = np.empty(count, dtype=np.float64)
    transform_gradients = np.empty((count, 3), dtype=np.float64)
    shear_values = np.empty(count, dtype=np.float64)
    shear_relief_gradients = np.empty((count, 3), dtype=np.float64)
    for i in prange(count):
        transform_raw, transform_dn, transform_ds = transform_strength_with_partials(
            closing[i], shear[i], smoothing=smoothing
        )
        shear_raw, shear_dn, shear_ds = shear_strength_with_partials(
            closing[i], shear[i], smoothing=smoothing
        )
        distance = abs(plane_distance[i])
        distance_sign = 0.0
        if plane_distance[i] > 0.0:
            distance_sign = 1.0
        elif plane_distance[i] < 0.0:
            distance_sign = -1.0

        width, height, detail_strength = transform_parameters
        profile, profile_d, _ = fault_profile_with_partials(distance, width)
        factor = (
            1.0
            if len(detail_weights) == 0
            else 1.0 + detail_strength * (2.0 * detail_weights[i] - 1.0)
        )
        motion = saturating_response(transform_raw, scale=response_scale)
        motion_chain = saturating_response_derivative(
            transform_raw, scale=response_scale
        )
        base = profile * (motion * factor) * height
        transform_values[i] = base
        for axis in range(3):
            motion_gradient = (
                transform_dn * closing_gradients[i, axis]
                + transform_ds * shear_motion_gradients[i, axis]
            ) * motion_chain
            factor_gradient = (
                0.0
                if len(detail_weights) == 0
                else detail_strength * 2.0 * detail_weight_gradients[i, axis]
            )
            distance_gradient = distance_sign * plane_distance_gradients[i, axis]
            transform_gradients[i, axis] = (
                height
                * factor
                * (profile_d * distance_gradient * motion + profile * motion_gradient)
                + profile * motion * height * factor_gradient
            )

        width, height, detail_strength = shear_parameters
        profile, profile_d, _ = fault_profile_with_partials(distance, width)
        factor = (
            1.0
            if len(detail_weights) == 0
            else 1.0 + detail_strength * (2.0 * detail_weights[i] - 1.0)
        )
        motion = saturating_response(shear_raw, scale=response_scale)
        motion_chain = saturating_response_derivative(shear_raw, scale=response_scale)
        base = profile * (motion * factor) * height
        shear_values[i] = base
        for axis in range(3):
            motion_gradient = (
                shear_dn * closing_gradients[i, axis]
                + shear_ds * shear_motion_gradients[i, axis]
            ) * motion_chain
            factor_gradient = (
                0.0
                if len(detail_weights) == 0
                else detail_strength * 2.0 * detail_weight_gradients[i, axis]
            )
            distance_gradient = distance_sign * plane_distance_gradients[i, axis]
            shear_relief_gradients[i, axis] = (
                height
                * factor
                * (profile_d * distance_gradient * motion + profile * motion_gradient)
                + profile * motion * height * factor_gradient
            )
    return transform_values, transform_gradients, shear_values, shear_relief_gradients


_fault_responses_serial = njit(cache=True)(_fault_responses_with_gradient)


@njit(cache=True, parallel=True)
def _fault_responses_parallel(
    plane_distance: np.ndarray,
    closing: np.ndarray,
    shear: np.ndarray,
    plane_distance_gradients: np.ndarray,
    closing_gradients: np.ndarray,
    shear_motion_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    transform_parameters: tuple[float, float, float],
    shear_parameters: tuple[float, float, float],
    smoothing: float,
    response_scale: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return _fault_responses_with_gradient(
        plane_distance,
        closing,
        shear,
        plane_distance_gradients,
        closing_gradients,
        shear_motion_gradients,
        detail_weights,
        detail_weight_gradients,
        transform_parameters,
        shear_parameters,
        smoothing,
        response_scale,
    )


def fault_responses_with_gradient(
    plane_distance: np.ndarray,
    closing: np.ndarray,
    shear: np.ndarray,
    plane_distance_gradients: np.ndarray,
    closing_gradients: np.ndarray,
    shear_motion_gradients: np.ndarray,
    detail_weights: np.ndarray,
    detail_weight_gradients: np.ndarray,
    transform_parameters: tuple[float, float, float],
    shear_parameters: tuple[float, float, float],
    smoothing: float,
    response_scale: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return unweighted transform values/gradients, then shear values/gradients.

    Motion saturation and detail are included; overlap weighting is not.
    ``closing`` is positive for convergence. Empty detail weights disable detail.
    """
    evaluator = _fault_responses_serial
    if len(plane_distance) >= 1024:
        evaluator = _fault_responses_parallel
    return evaluator(
        plane_distance,
        closing,
        shear,
        plane_distance_gradients,
        closing_gradients,
        shear_motion_gradients,
        detail_weights,
        detail_weight_gradients,
        transform_parameters,
        shear_parameters,
        smoothing,
        response_scale,
    )
