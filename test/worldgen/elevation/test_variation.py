from dataclasses import replace

import numpy as np

from src.worldgen.elevation.config import TerrainVariationConfig
from src.worldgen.elevation.variation import TerrainVariationField
from src.worldgen.geometry import generate_icosphere


def test_amplitude_controls_bounded_signed_displacement():
    positions, _ = generate_icosphere(5)
    config = TerrainVariationConfig(amplitude_percent=0.01)
    field = TerrainVariationField(config, noise_seed=17)
    values = field.sample(positions, radius_m=1_000_000.0)
    doubled = replace(
        field,
        config=replace(config, amplitude_percent=0.02),
    ).sample(positions, radius_m=1_000_000.0)
    disabled = replace(
        field,
        config=replace(config, amplitude_percent=0.0),
    ).sample(positions, radius_m=1_000_000.0)

    assert np.any(values > 0.0)
    assert np.any(values < 0.0)
    assert np.max(np.abs(values)) <= 100.0
    np.testing.assert_array_equal(doubled, values * 2.0)
    np.testing.assert_array_equal(disabled, np.zeros(len(positions)))


def test_fraction_sampling_is_volumetric_immutable_and_query_independent():
    positions = np.random.default_rng(411).uniform(-1.6, 1.6, size=(257, 3))
    assert np.any(np.linalg.norm(positions, axis=1) != 1.0)

    config = TerrainVariationConfig(amplitude_percent=0.4)
    field = TerrainVariationField(config, noise_seed=17)
    values = field.sample_fraction(positions)

    assert np.all(np.isfinite(values))
    assert np.min(values) < 0.0 < np.max(values)
    assert np.max(np.abs(values)) <= config.amplitude_percent / 100.0
    assert not values.flags.writeable
    np.testing.assert_array_equal(field.sample_fraction(positions), values)
    np.testing.assert_array_equal(
        np.concatenate(
            (
                field.sample_fraction(positions[:71]),
                field.sample_fraction(positions[71:193]),
                field.sample_fraction(positions[193:]),
            )
        ),
        values,
    )
    permutation = np.random.default_rng(29).permutation(len(positions))
    np.testing.assert_array_equal(
        field.sample_fraction(positions[permutation]), values[permutation]
    )

    doubled = replace(
        field,
        config=replace(config, amplitude_percent=0.8),
    ).sample_fraction(positions)
    np.testing.assert_array_equal(doubled, 2.0 * values)

    disabled = replace(
        field,
        config=replace(config, amplitude_percent=0.0),
    ).sample_fraction(positions)
    empty = field.sample_fraction(np.empty((0, 3)))
    for zeros in (disabled, empty):
        assert zeros.dtype == np.float64
        assert not zeros.flags.writeable
        np.testing.assert_array_equal(zeros, np.zeros(len(zeros)))


def test_variation_is_continuous_across_spherical_coordinate_seams():
    field = TerrainVariationField(TerrainVariationConfig(), noise_seed=17)
    positions = np.array(
        [
            [-1.0, -1e-7, 0.2],
            [-1.0, 1e-7, 0.2],
            [-1e-7, 0.0, 1.0],
            [1e-7, 0.0, 1.0],
        ]
    )
    positions /= np.linalg.norm(positions, axis=1, keepdims=True)
    values = field.sample(positions, radius_m=6_371_000.0)

    assert abs(values[0] - values[1]) < 0.01
    assert abs(values[2] - values[3]) < 0.01
