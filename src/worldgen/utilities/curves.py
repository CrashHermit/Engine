"""Reusable scalar curve functions."""

import numpy as np
from numba.extending import register_jitable


@register_jitable
def clamp_unit(value: float) -> float:
    """Clamp a scalar to the closed unit interval."""
    return min(max(value, 0.0), 1.0)


@register_jitable
def smoothstep_scalar(value: float) -> float:
    """Return clamped cubic smoothstep without array operations."""
    clipped = clamp_unit(value)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def smoothstep(values: np.ndarray) -> np.ndarray:
    """Return the clamped cubic smoothstep curve."""
    clipped = np.clip(values, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


@register_jitable
def smoothstep_derivative_scalar(value: float) -> float:
    """Return the derivative of clamped cubic smoothstep."""
    if value <= 0.0 or value >= 1.0:
        return 0.0
    return 6.0 * value * (1.0 - value)


def smoothstep_derivative(values: np.ndarray) -> np.ndarray:
    """Return the derivative of clamped cubic smoothstep for arrays."""
    clipped = np.clip(values, 0.0, 1.0)
    return np.where(
        (values > 0.0) & (values < 1.0), 6.0 * clipped * (1.0 - clipped), 0.0
    )


def smooth_upper_bound(
    values: np.ndarray, *, upper: float, transition_half_width: float
) -> np.ndarray:
    """Cap values with a C1 quadratic knee around a positive upper bound.

    Below ``upper - transition_half_width`` the input is unchanged. Above
    ``upper + transition_half_width`` the result is exactly ``upper``.
    Positive half-widths preserve value and first-derivative continuity at
    both joins; this is not a globally analytic saturation.
    """
    values = np.asarray(values, dtype=np.float64)
    lower = upper - transition_half_width
    position = np.clip((values - lower) / (2.0 * transition_half_width), 0.0, 1.0)
    rounded = lower + transition_half_width * position * (2.0 - position)
    return np.where(values <= lower, values, rounded)


def smooth_upper_bound_derivative(
    values: np.ndarray, *, upper: float, transition_half_width: float
) -> np.ndarray:
    """Return the derivative of :func:`smooth_upper_bound` by input value."""
    lower = upper - transition_half_width
    position = np.clip((values - lower) / (2.0 * transition_half_width), 0.0, 1.0)
    return np.where(
        values <= lower,
        1.0,
        np.where(values >= upper + transition_half_width, 0.0, 1.0 - position),
    )


@register_jitable
def saturating_response(values: np.ndarray | float, scale: float) -> np.ndarray | float:
    """Smoothly saturate signed motion amplitudes without changing their sign."""
    return values / np.hypot(values, scale)


@register_jitable
def saturating_response_derivative(
    values: np.ndarray | float, scale: float
) -> np.ndarray | float:
    """Return the derivative of :func:`saturating_response` by input value.

    The caller supplies a positive scale.
    """
    denominator = np.hypot(values, scale)
    return scale * scale / (denominator * denominator * denominator)
