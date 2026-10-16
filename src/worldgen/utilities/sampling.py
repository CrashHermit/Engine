"""Seed selection over fixed spherical candidate positions."""

import numpy as np


def poisson_disk_sample(
    positions: np.ndarray,
    num_points: int,
    min_distance: float,
    *,
    rng: np.random.Generator,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    """Select spaced candidate indices in one randomized greedy pass."""
    selected: list[int] = []
    if weights is None:
        candidates = rng.permutation(len(positions))
    else:
        priorities = -np.log(rng.random(len(positions))) / weights
        candidates = np.argsort(priorities)
    for candidate in candidates:
        candidate_index = int(candidate)
        if not selected:
            selected.append(candidate_index)
        else:
            distances = np.linalg.norm(
                positions[np.asarray(selected)] - positions[candidate_index], axis=1
            )
            if np.all(distances >= min_distance):
                selected.append(candidate_index)
        if len(selected) == num_points:
            break
    return np.asarray(selected, dtype=np.int64)
