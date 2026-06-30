import numpy as np
import opensimplex as osn


def generate_3d_fbm(
    coordinates: np.ndarray,
    octaves: int,
    base_frequency: float,
    lacunarity: float,
    persistence: float,
) -> np.ndarray:
    """Return FBm noise over ``coordinates`` (shape ``(n, 3)").

    Args:
        coordinates: Per-point 3-D positions, shape ``(n, 3)".
        octaves: Number of FBm octaves.
        base_frequency: Starting spatial frequency.
        lacunarity: Frequency multiplier between octaves.
        persistence: Amplitude multiplier between octaves.

    Returns:
        Raw noise values, shape ``(n,)".
    """
    n: int = len(coordinates)
    values: np.ndarray = np.zeros(n, dtype=np.double)

    amplitude: float = 1.0
    frequency: float = base_frequency

    for octave in range(octaves):
        shift: float = octave * 1123.456

        noise_layer: np.ndarray = np.zeros_like(values)
        for i in range(n):
            noise_layer[i] = osn.noise3(
                (coordinates[i, 0] * frequency) + shift,
                (coordinates[i, 1] * frequency) + shift,
                (coordinates[i, 2] * frequency) + shift,
            )

        values += noise_layer * amplitude

        amplitude *= persistence
        frequency *= lacunarity

    return values

def generate_spaced_seeds(
    coordinates: np.ndarray,
    num_points: int,
    min_distance: float,
    max_retries: int,
    valid_indices: np.ndarray | None = None,
) -> list[int]:
    """Greedy Poisson-disk sampling over a fixed candidate set.

    Repeatedly picks a random candidate, keeps it if it is at least
    ``min_distance`` from every already-selected seed, and resets its
    retry counter.  Stops when ``num_points`` seeds are found or
    ``max_retries"" consecutive failures are exhausted.

    Args:
        coordinates: Candidate positions, shape ``(n, 3)".
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
        valid_indices = np.arange(len(coordinates))

    if len(valid_indices) == 0:
        msg = "valid_indices is empty, can't generate seeds."
        raise ValueError(msg)

    while len(seed_indices) < num_points and retries < max_retries:
        candidate_idx: int = int(np.random.choice(valid_indices))

        if not seed_indices:
            seed_indices.append(candidate_idx)
            retries = 0
            continue

        candidate_xyz: np.ndarray = coordinates[candidate_idx]
        seeds_xyz: np.ndarray = coordinates[seed_indices]

        distances: np.ndarray = np.linalg.norm(seeds_xyz - candidate_xyz, axis=1)

        if np.min(distances) >= min_distance:
            seed_indices.append(candidate_idx)
            retries = 0
        else:
            retries += 1

    if retries >= max_retries:
        print(f"Only found {len(seed_indices)} seeds before hitting max retries.")

    return seed_indices
