import numpy as np

from src.worldgen.field.noise import NoiseConfig, fbm, normalized_noise


def _sample(positions, seed=123, *, frequency=1.4, octaves=5):
    return fbm(
        positions,
        seed=seed,
        octaves=octaves,
        base_frequency=frequency,
        lacunarity=2.0,
        persistence=0.6,
    )


def _positions():
    positions = np.random.default_rng(21).normal(size=(17, 3))
    return positions / np.linalg.norm(positions, axis=1, keepdims=True)


def test_seeded_fields_are_isolated_and_preserve_global_numpy_state():
    positions = _positions()
    before = np.random.get_state()
    first = _sample(positions, seed=2**60 + 123)
    other = _sample(positions, seed=2**60 + 456)
    repeated = _sample(positions, seed=2**60 + 123)
    after = np.random.get_state()
    np.testing.assert_array_equal(first, repeated)
    assert not np.array_equal(first, other)
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_sampling_is_independent_of_batch_order_and_subset():
    positions = _positions()
    order = np.array([16, 2, 10, 0, 9, 4])
    full = _sample(positions)
    subset = _sample(positions[order])
    np.testing.assert_array_equal(subset, full[order])
    singles = np.array([_sample(positions[i : i + 1])[0] for i in order])
    np.testing.assert_array_equal(singles, subset)


def test_noise_frequency_matches_coordinate_scaling_and_nearby_points_are_close():
    positions = _positions()
    np.testing.assert_array_equal(
        _sample(positions, frequency=2.0, octaves=1),
        _sample(positions * 2.0, frequency=1.0, octaves=1),
    )
    original = _sample(positions, frequency=1.0, octaves=1)
    nearby = _sample(positions + 1e-5, frequency=1.0, octaves=1)
    assert np.all(np.abs(original - nearby) < 0.001)


def test_world_seeds_wrap_consistently_into_signed_32_bit_noise_seeds():
    positions = _positions()
    np.testing.assert_array_equal(
        _sample(positions, seed=2**31 + 17),
        _sample(positions, seed=-(2**31) + 17),
    )
    np.testing.assert_array_equal(
        _sample(positions, seed=-(2**60) + 17),
        _sample(positions, seed=17),
    )


def test_normalized_noise_has_fixed_mapping_across_query_batches():
    points = _positions()
    config = NoiseConfig()
    full = normalized_noise(points, config, seed=17)
    subset = normalized_noise(points[[4, 1, 8]], config, seed=17)
    single = normalized_noise(points[4:5], config, seed=17)
    np.testing.assert_array_equal(subset, full[[4, 1, 8]])
    np.testing.assert_array_equal(single, full[4:5])
    assert np.all((full >= 0.0) & (full <= 1.0))
