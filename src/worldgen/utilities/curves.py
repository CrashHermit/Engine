"""Reusable scalar curve functions."""

import numpy as np


def clamp_unit(value: float) -> float:
    """Clamp a scalar to the closed unit interval."""
    return min(max(value, 0.0), 1.0)


def smoothstep_scalar(value: float) -> float:
    """Return clamped cubic smoothstep without array operations."""
    clipped = clamp_unit(value)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def smoothstep(values: np.ndarray) -> np.ndarray:
    """Return the clamped cubic smoothstep curve."""
    clipped = np.clip(values, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)
