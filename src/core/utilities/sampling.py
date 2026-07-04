"""Sampling utilities — seed placement and point selection over meshes."""

import numpy as np


def poisson_disk_sample(
    positions: np.ndarray,
    num_points: int,
    min_distance: float,
    max_retries: int,
    valid_indices: np.ndarray | None = None,
) -> list[int]:
    """Greedy Poisson-disk sampling over a fixed candidate set.

    Repeatedly picks a random candidate, keeps it if it is at least
    ``min_distance`` from every already-selected seed, and resets its
    retry counter.  Stops when ``num_points`` seeds are found or
    ``max_retries`` consecutive failures are exhausted.

    Args:
        positions: Candidate positions, shape ``(n, 3)``.
        num_points: Target number of seeds to place.
        min_distance: Minimum Euclidean separation between seeds.
        max_retries: Consecutive failures before giving up.
        valid_indices: Candidate indices to draw from; defaults to all.

    Returns:
        Selected seed indices (length ≤ ``num_points``).
    """
    seed_indices: list[int] = []
    retries: int = 0

    if valid_indices is None:
        valid_indices = np.arange(len(positions))

    if len(valid_indices) == 0:
        msg = "valid_indices is empty, can't generate seeds."
        raise ValueError(msg)

    while len(seed_indices) < num_points and retries < max_retries:
        candidate_idx: int = int(np.random.choice(valid_indices))

        if not seed_indices:
            seed_indices.append(candidate_idx)
            retries = 0
            continue

        candidate_xyz: np.ndarray = positions[candidate_idx]
        seeds_xyz: np.ndarray = positions[seed_indices]

        distances: np.ndarray = np.linalg.norm(seeds_xyz - candidate_xyz, axis=1)

        if np.min(distances) >= min_distance:
            seed_indices.append(candidate_idx)
            retries = 0
        else:
            retries += 1

    if retries >= max_retries:
        print(f"Only found {len(seed_indices)} seeds before hitting max retries.")

    return seed_indices
