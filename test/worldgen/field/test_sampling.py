import numpy as np

from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.utilities.sampling import poisson_disk_sample


def test_poisson_sampling_is_reproducible_and_spaced() -> None:
    positions, _ = generate_icosphere(3)
    first = poisson_disk_sample(positions, 5, 0.1, rng=np.random.default_rng(12))
    second = poisson_disk_sample(positions, 5, 0.1, rng=np.random.default_rng(12))

    np.testing.assert_array_equal(first, second)
    assert len(np.unique(first)) == 5
    distances = positions[first][:, None] - positions[first][None, :]
    distances += np.eye(len(first))[:, :, None]
    pairwise = np.linalg.norm(distances, axis=2)
    assert np.all(pairwise[np.triu_indices(len(first), k=1)] >= 0.1)


def test_weighted_poisson_placement_prioritizes_a_deterministically_weighted_candidate():
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    # Candidate 4 is far from all others; its overwhelming synthetic weight makes
    # its exponential-race priority deterministic without a statistical threshold.
    weights = np.array([1e-300, 1e-300, 1e-300, 1e-300, 1e300])

    selected = poisson_disk_sample(
        positions,
        1,
        0.0,
        rng=np.random.default_rng(7),
        weights=weights,
    )

    np.testing.assert_array_equal(selected, [4])
