import numpy as np

from src.worldgen.field.seeds import generate_direction_seeds, generate_seed_cloud


def test_seed_cloud_reproducibility_without_touching_global_rng():
    before = np.random.get_state()
    actual = generate_seed_cloud(12, rng=np.random.default_rng(31))
    after = np.random.get_state()
    repeated = generate_seed_cloud(12, rng=np.random.default_rng(31))

    np.testing.assert_array_equal(actual, repeated)
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


def test_direction_seeds_are_reproducible_and_isotropic():
    before = np.random.get_state()
    seeds = generate_direction_seeds(8192, rng=np.random.default_rng(31))
    after = np.random.get_state()
    repeated = generate_direction_seeds(8192, rng=np.random.default_rng(31))
    different = generate_direction_seeds(8192, rng=np.random.default_rng(32))
    np.testing.assert_array_equal(seeds, repeated)
    assert not np.array_equal(seeds, different)
    assert seeds.shape == (8192, 3)
    assert seeds.dtype == np.float64
    assert not seeds.flags.writeable
    directions = seeds / np.linalg.norm(seeds, axis=1)[:, None]
    assert np.all(np.abs(directions.mean(axis=0)) < 0.03)
    np.testing.assert_allclose((directions**2).mean(axis=0), 1 / 3, atol=0.03)
    np.testing.assert_allclose((directions**4).mean(axis=0), 1 / 5, atol=0.015)
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_empty_direction_seeds_preserve_shape_and_immutability():
    seeds = generate_direction_seeds(0, rng=np.random.default_rng(7))
    assert seeds.shape == (0, 3)
    assert seeds.dtype == np.float64
    assert not seeds.flags.writeable
