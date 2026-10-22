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
