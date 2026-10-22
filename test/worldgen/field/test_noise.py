import numpy as np

from src.worldgen.field.noise import (
    fbm_with_gradient,
    noise_multiplier_with_gradient,
    normalized_noise_with_gradient,
    sample_vector_noise_with_jacobian,
)

from src.worldgen.field.noise import (
    NoiseConfig,
    fbm,
    noise_multiplier,
    normalized_noise,
    sample_vector_noise,
)


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


def test_vector_noise_has_independent_signed_channels_and_batch_invariance():
    positions = _positions()
    config = NoiseConfig(octaves=3, base_frequency=1.2)
    seeds = (18, 44, 78)

    before = np.random.get_state()
    full = sample_vector_noise(positions, config, seeds=seeds)
    repeated = sample_vector_noise(positions, config, seeds=seeds)
    other = sample_vector_noise(positions, config, seeds=(19, 45, 79))
    after = np.random.get_state()

    expected = np.column_stack(
        [normalized_noise(positions, config, seed=seed) * 2.0 - 1.0 for seed in seeds]
    )
    np.testing.assert_array_equal(full, expected)
    np.testing.assert_array_equal(full, repeated)
    assert full.shape == (len(positions), 3)
    assert full.dtype == np.float64
    assert np.all((full >= -1.0) & (full <= 1.0))
    assert not np.array_equal(full, other)
    np.testing.assert_array_equal(
        sample_vector_noise(positions[[7, 0, 3]], config, seeds=seeds),
        full[[7, 0, 3]],
    )
    assert sample_vector_noise(np.empty((0, 3)), config, seeds=seeds).shape == (
        0,
        3,
    )
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_analytic_noise_gradients_match_diagnostic_finite_differences():
    points = _positions()[:5]
    config = NoiseConfig(octaves=3, base_frequency=1.1)
    sample = normalized_noise_with_gradient(points, config, seed=72)
    # Resolve float32 octave offsets while keeping the noise locally linear.
    epsilon = 3e-3
    finite = np.column_stack(
        [
            (
                normalized_noise(points + np.eye(3)[axis] * epsilon, config, seed=72)
                - normalized_noise(points - np.eye(3)[axis] * epsilon, config, seed=72)
            )
            / (2.0 * epsilon)
            for axis in range(3)
        ]
    )
    assert np.linalg.norm(sample.gradients - finite) < 0.015 * np.linalg.norm(
        sample.gradients
    )
    raw = fbm_with_gradient(
        points,
        seed=72,
        octaves=3,
        base_frequency=1.1,
        lacunarity=config.lacunarity,
        persistence=config.persistence,
    )
    raw_finite = 2 * sum(config.persistence**i for i in range(config.octaves)) * finite
    assert np.linalg.norm(raw.gradients - raw_finite) < 0.015 * np.linalg.norm(
        raw.gradients
    )
    vector = sample_vector_noise_with_jacobian(points, config, seeds=(1, 2, 3))
    vector_finite = np.stack(
        [
            (
                sample_vector_noise(
                    points + np.eye(3)[axis] * epsilon, config, seeds=(1, 2, 3)
                )
                - sample_vector_noise(
                    points - np.eye(3)[axis] * epsilon, config, seeds=(1, 2, 3)
                )
            )
            / (2 * epsilon)
            for axis in range(3)
        ],
        axis=2,
    )
    assert np.linalg.norm(vector.jacobians - vector_finite) < 0.025 * np.linalg.norm(
        vector.jacobians
    )
    multiplier = noise_multiplier_with_gradient(
        points, seed=72, frequency=0.8, strength=0.4
    )
    multiplier_finite = np.column_stack(
        [
            (
                noise_multiplier(
                    points + np.eye(3)[axis] * epsilon,
                    seed=72,
                    frequency=0.8,
                    strength=0.4,
                )
                - noise_multiplier(
                    points - np.eye(3)[axis] * epsilon,
                    seed=72,
                    frequency=0.8,
                    strength=0.4,
                )
            )
            / (2 * epsilon)
            for axis in range(3)
        ]
    )
    np.testing.assert_allclose(
        multiplier.gradients, multiplier_finite, rtol=2e-3, atol=2e-5
    )
