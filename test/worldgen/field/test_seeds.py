import numpy as np

from src.worldgen.field.seeds import generate_seed_cloud


def test_seed_cloud_matches_centered_generator_without_touching_global_rng():
    before = np.random.get_state()
    actual = generate_seed_cloud(12, rng=np.random.default_rng(31))
    after = np.random.get_state()
    expected = 2.0 * np.random.default_rng(31).random((12, 3)) - 1.0

    np.testing.assert_array_equal(actual, expected)
    assert actual.shape == (12, 3)
    assert actual.dtype == np.float64
    assert not actual.flags.writeable
    assert np.all((actual >= -1.0) & (actual <= 1.0))
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_empty_seed_cloud_has_three_coordinate_columns():
    seeds = generate_seed_cloud(0, rng=np.random.default_rng(7))

    assert seeds.shape == (0, 3)
    assert seeds.dtype == np.float64
    assert not seeds.flags.writeable
