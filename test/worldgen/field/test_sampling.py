import numpy as np

from src.worldgen.geometry import generate_icosphere
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
