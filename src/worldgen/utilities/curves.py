"""Reusable scalar curve functions."""

import numpy as np


def smoothstep(values: np.ndarray) -> np.ndarray:
    """Return the clamped cubic smoothstep curve."""
    clipped = np.clip(values, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)
