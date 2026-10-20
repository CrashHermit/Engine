"""Reusable compact influence curves for continuous fields."""

import numpy as np

from src.worldgen.utilities.curves import smoothstep


def compact_influence(distances: np.ndarray, *, width: float) -> np.ndarray:
    """Map nonnegative distances to a compact cubic influence profile."""
    influence = smoothstep(1.0 - np.asarray(distances, dtype=np.float64) / width)
    influence.setflags(write=False)
    return influence
