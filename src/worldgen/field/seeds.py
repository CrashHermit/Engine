"""Independent Cartesian position and isotropic direction seed sampling."""

import numpy as np


def generate_seed_cloud(count: int, *, rng: np.random.Generator) -> np.ndarray:
    """Return read-only float64 seed positions uniformly distributed in ``[-1, 1]³``."""
    seeds = 2.0 * rng.random((count, 3)) - 1.0
    seeds.setflags(write=False)
    return seeds


def generate_direction_seeds(count: int, *, rng: np.random.Generator) -> np.ndarray:
    """Return raw Gaussian axis seeds; consumers discard their magnitudes."""
    seeds = rng.normal(size=(count, 3))
    seeds.setflags(write=False)
    return seeds


def select_weighted_seeds(
    candidates: np.ndarray,
    weights: np.ndarray,
    count: int,
    *,
    rng: np.random.Generator,
) -> np.ndarray:
    """Select candidates without replacement using trusted nonnegative weights."""
    if count == 0:
        selected = candidates[:0].copy()
    else:
        probabilities = np.asarray(weights, dtype=np.float64)
        probabilities = probabilities / probabilities.sum()
        indices = rng.choice(
            len(candidates), size=count, replace=False, p=probabilities
        )
        selected = candidates[indices]
    selected.setflags(write=False)
    return selected
