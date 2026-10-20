"""Centered Cartesian seed positions for normalized world fields."""

import numpy as np


def generate_seed_cloud(count: int, *, rng: np.random.Generator) -> np.ndarray:
    """Return read-only float64 seed positions uniformly distributed in ``[-1, 1]³``."""
    seeds = 2.0 * rng.random((count, 3)) - 1.0
    seeds.setflags(write=False)
    return seeds
