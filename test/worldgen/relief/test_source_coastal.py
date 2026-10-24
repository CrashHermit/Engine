from dataclasses import replace

import numpy as np

from src.worldgen.relief.coastal import (
    SourceCoastalConfig,
    SourceCoastalSpanConfig,
    SourceCoastalField,
    coastal_height_profile,
    coastal_height_profile_with_partials,
)
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import noise_multiplier, noise_multiplier_with_gradient

REFERENCE_RADIUS_M = 6_371_000.0


def _zero_gradient(sample):
    def sample_with_gradient(points):
        return ScalarSample(
            sample(points), np.zeros((len(points), 3), dtype=np.float64)
        )

    return sample_with_gradient


def _linear_weight_with_gradient(points):
    return ScalarSample(
        (points[:, 0] + 1.0) / 2.0,
        np.tile([0.5, 0.0, 0.0], (len(points), 1)),
    )


def _noise_anomaly_with_gradient(points, *, seed, strength):
    sample = noise_multiplier_with_gradient(
        points, seed=seed, frequency=1.0, strength=strength
    )
    return ScalarSample(sample.values - 1.0, sample.gradients)


def _span_noise_field(
    *,
    inland_strength: float = 0.0,
    shelf_strength: float = 0.0,
    slope_strength: float = 0.0,
    density_strength: float = 0.0,
) -> SourceCoastalField:
    return SourceCoastalField(
        sample_continental_weight=lambda points: (points[:, 0] + 1.0) / 2.0,
        sample_density_anomaly=lambda points: (
            noise_multiplier(points, seed=53, frequency=1.0, strength=density_strength)
            - 1.0
        ),
        influence_span_noise_seeds=(41, 43, 47),
        sample_continental_weight_with_gradient=_linear_weight_with_gradient,
        sample_density_anomaly_with_gradient=lambda points: (
            _noise_anomaly_with_gradient(points, seed=53, strength=density_strength)
        ),
        config=SourceCoastalConfig(
            coastline_weight=0.7,
            inland=SourceCoastalSpanConfig(0.2, inland_strength, 1.0),
            shelf=SourceCoastalSpanConfig(0.15, shelf_strength, 1.0),
            slope=SourceCoastalSpanConfig(0.25, slope_strength, 1.0),
            interior_height_percent=10.0,
            shelf_depth_percent=3.0,
            basin_depth_percent=80.0,
            continental_buoyancy_percent=20.0,
            oceanic_buoyancy_percent=40.0,
        ),
    )


def test_coastal_profile_has_stable_margin_and_shelf_break_landmarks():
    widths = np.array([0.07, 0.08, 0.09, 0.1, 0.11])
    margins = np.array([0.07, 0.08, 0.09, 0.1, 0.11])
    coastline = coastal_height_profile(
        margins,
        inland_width=np.linspace(0.12, 0.16, len(margins)),
        shelf_width=widths,
        slope_width=np.linspace(0.06, 0.1, len(margins)),
        interior_height=np.linspace(0.05, 0.15, len(margins)),
        shelf_depth=0.03,
        basin_depth=np.linspace(0.6, 0.9, len(margins)),
    )
    np.testing.assert_array_equal(coastline, np.zeros(len(margins)))

    shelf_break = coastal_height_profile(
        np.zeros(5),
        inland_width=np.linspace(0.12, 0.16, 5),
        shelf_width=widths,
        slope_width=np.linspace(0.06, 0.1, 5),
        interior_height=np.linspace(0.05, 0.15, 5),
        shelf_depth=0.03,
        basin_depth=np.linspace(0.6, 0.9, 5),
    )
    np.testing.assert_allclose(shelf_break, -0.03, atol=1e-15)


def test_density_changes_saturated_material_relief_not_coast_landmarks():
    positions = np.zeros((4, 3))
    weights = np.array([1.0, 0.65, 0.5, 0.0])

    def sample(density):
        field = SourceCoastalField(
            sample_continental_weight=lambda points: np.full(len(points), 0.5),
            sample_density_anomaly=lambda points: np.full(len(points), density),
            influence_span_noise_seeds=(3, 5, 7),
            sample_continental_weight_with_gradient=_zero_gradient(
                lambda points: np.full(len(points), 0.5)
            ),
            sample_density_anomaly_with_gradient=_zero_gradient(
                lambda points: np.full(len(points), density)
            ),
            config=SourceCoastalConfig(
                inland=SourceCoastalSpanConfig(0.2, 0.0),
                shelf=SourceCoastalSpanConfig(0.15, 0.0),
                slope=SourceCoastalSpanConfig(0.25, 0.0),
                interior_height_percent=10.0,
                shelf_depth_percent=3.0,
                basin_depth_percent=80.0,
                continental_buoyancy_percent=20.0,
                oceanic_buoyancy_percent=40.0,
            ),
        )
        return field.sample_from_weight(positions, weights).elevation

    baseline = sample(0.0)
    varied = sample(0.5)
    np.testing.assert_allclose(baseline[1], 0.0, atol=1e-15)
    np.testing.assert_allclose(varied[1], baseline[1], atol=1e-15)
    np.testing.assert_allclose(baseline[2], -0.03, atol=1e-15)
    np.testing.assert_allclose(varied[2], baseline[2], atol=1e-15)
    assert varied[0] != baseline[0]
    assert varied[3] != baseline[3]


def test_source_coastal_field_has_expected_profile_and_read_only_samples():
    config = SourceCoastalConfig(
        inland=SourceCoastalSpanConfig(0.2, 0.0),
        shelf=SourceCoastalSpanConfig(0.15, 0.0),
        slope=SourceCoastalSpanConfig(0.25, 0.0),
        interior_height_percent=10.0,
        shelf_depth_percent=3.0,
        basin_depth_percent=80.0,
        continental_buoyancy_percent=20.0,
        oceanic_buoyancy_percent=40.0,
    )
    field = SourceCoastalField(
        sample_continental_weight=lambda points: np.zeros(len(points)),
        sample_density_anomaly=lambda points: np.zeros(len(points)),
        influence_span_noise_seeds=(11, 13, 17),
        sample_continental_weight_with_gradient=_zero_gradient(
            lambda points: np.zeros(len(points))
        ),
        sample_density_anomaly_with_gradient=_zero_gradient(
            lambda points: np.zeros(len(points))
        ),
        config=config,
    )
    weights = np.array([0.85, 0.65, 0.5, 0.25, 0.0])
    sample = field.sample_from_weight(np.zeros((len(weights), 3)), weights)

    np.testing.assert_array_equal(sample.continental_weight, weights)
    np.testing.assert_allclose(sample.elevation, [0.1, 0.0, -0.03, -0.8, -0.8])
    assert not sample.continental_weight.flags.writeable
    assert not sample.elevation.flags.writeable
    assert field.sample_elevation(np.zeros((1, 3)))[0] == -0.8


def test_continental_and_oceanic_baselines_are_independently_configurable():
    config = SourceCoastalConfig(
        inland=SourceCoastalSpanConfig(0.2, 0.0),
        shelf=SourceCoastalSpanConfig(0.15, 0.0),
        slope=SourceCoastalSpanConfig(0.25, 0.0),
        interior_height_percent=100.0 * 600.0 / REFERENCE_RADIUS_M,
        shelf_depth_percent=100.0 * 200.0 / REFERENCE_RADIUS_M,
        basin_depth_percent=100.0 * 4500.0 / REFERENCE_RADIUS_M,
    )

    def sample(active_config):
        field = SourceCoastalField(
            sample_continental_weight=lambda points: np.zeros(len(points)),
            sample_density_anomaly=lambda points: np.zeros(len(points)),
            influence_span_noise_seeds=(11, 13, 17),
            sample_continental_weight_with_gradient=_zero_gradient(
                lambda points: np.zeros(len(points))
            ),
            sample_density_anomaly_with_gradient=_zero_gradient(
                lambda points: np.zeros(len(points))
            ),
            config=active_config,
        )
        weights = np.array([1.0, 0.65, 0.5, 0.0])
        return (
            field.sample_from_weight(np.zeros((len(weights), 3)), weights).elevation
            * REFERENCE_RADIUS_M
        )

    baseline = sample(config)
    np.testing.assert_allclose(baseline, [600.0, 0.0, -200.0, -4500.0])

    taller_continent = sample(
        replace(
            config,
            interior_height_percent=100.0 * 1200.0 / REFERENCE_RADIUS_M,
        )
    )
    np.testing.assert_allclose(taller_continent, [1200.0, 0.0, -200.0, -4500.0])
    np.testing.assert_array_equal(taller_continent[1:], baseline[1:])

    deeper_ocean = sample(
        replace(config, basin_depth_percent=100.0 * 6000.0 / REFERENCE_RADIUS_M)
    )
    np.testing.assert_allclose(deeper_ocean, [600.0, 0.0, -200.0, -6000.0])
    np.testing.assert_array_equal(deeper_ocean[:3], baseline[:3])


def test_coastline_offset_and_shelf_width_use_continental_influence_units():
    positions = np.zeros((3, 3))
    weights = np.array([0.7, 0.6, 0.5])

    def sample(shelf_width):
        field = SourceCoastalField(
            sample_continental_weight=lambda points: np.full(len(points), 0.7),
            sample_density_anomaly=lambda points: np.zeros(len(points)),
            influence_span_noise_seeds=(1, 2, 3),
            sample_continental_weight_with_gradient=_zero_gradient(
                lambda points: np.full(len(points), 0.7)
            ),
            sample_density_anomaly_with_gradient=_zero_gradient(
                lambda points: np.zeros(len(points))
            ),
            config=SourceCoastalConfig(
                coastline_weight=0.7,
                inland=SourceCoastalSpanConfig(0.2, 0.0),
                shelf=SourceCoastalSpanConfig(shelf_width, 0.0),
                slope=SourceCoastalSpanConfig(0.2, 0.0),
                interior_height_percent=10.0,
                shelf_depth_percent=3.0,
                basin_depth_percent=80.0,
                continental_buoyancy_percent=20.0,
                oceanic_buoyancy_percent=40.0,
            ),
        )
        return field.sample_from_weight(positions, weights).elevation

    np.testing.assert_allclose(sample(0.1), [0.0, -0.03, -0.415], atol=1e-15)
    np.testing.assert_allclose(sample(0.2), [0.0, -0.015, -0.03], atol=1e-15)


def test_span_variation_does_not_move_configured_coastline():
    positions = np.random.default_rng(912).uniform(-1.0, 1.0, size=(257, 3))
    field = SourceCoastalField(
        sample_continental_weight=lambda points: np.full(len(points), 0.7),
        sample_density_anomaly=lambda points: (
            noise_multiplier(points, seed=31, frequency=1.0, strength=0.4) - 1.0
        ),
        influence_span_noise_seeds=(17, 19, 23),
        sample_continental_weight_with_gradient=_zero_gradient(
            lambda points: np.full(len(points), 0.7)
        ),
        sample_density_anomaly_with_gradient=lambda points: (
            _noise_anomaly_with_gradient(points, seed=31, strength=0.4)
        ),
        config=SourceCoastalConfig(
            coastline_weight=0.7,
            inland=SourceCoastalSpanConfig(0.2, 0.8),
            shelf=SourceCoastalSpanConfig(0.15, 0.8),
            slope=SourceCoastalSpanConfig(0.25, 0.8),
            interior_height_percent=10.0,
            shelf_depth_percent=3.0,
            basin_depth_percent=80.0,
            continental_buoyancy_percent=20.0,
            oceanic_buoyancy_percent=40.0,
        ),
    )

    np.testing.assert_array_equal(
        field.sample(positions).elevation, np.zeros(len(positions))
    )


def test_source_coastal_sampling_is_query_set_independent_and_varies_spans():
    positions = np.random.default_rng(832).uniform(-1.0, 1.0, size=(129, 3))
    config = SourceCoastalConfig(
        inland=SourceCoastalSpanConfig(0.2, 0.7, 1.1),
        shelf=SourceCoastalSpanConfig(0.15, 0.7, 1.1),
        slope=SourceCoastalSpanConfig(0.25, 0.7, 1.1),
        interior_height_percent=10.0,
        shelf_depth_percent=3.0,
        basin_depth_percent=80.0,
        continental_buoyancy_percent=20.0,
        oceanic_buoyancy_percent=40.0,
    )
    field = SourceCoastalField(
        sample_continental_weight=lambda points: (points[:, 0] + 1.0) / 2.0,
        sample_density_anomaly=lambda points: (
            noise_multiplier(points, seed=31, frequency=1.0, strength=0.4) - 1.0
        ),
        influence_span_noise_seeds=(41, 43, 47),
        sample_continental_weight_with_gradient=_linear_weight_with_gradient,
        sample_density_anomaly_with_gradient=lambda points: (
            _noise_anomaly_with_gradient(points, seed=31, strength=0.4)
        ),
        config=config,
    )
    repeat = field.sample(positions)
    np.testing.assert_array_equal(field.sample(positions).elevation, repeat.elevation)

    split = np.concatenate(
        [
            field.sample(positions[:37]).elevation,
            field.sample(positions[37:91]).elevation,
            field.sample(positions[91:]).elevation,
        ]
    )
    np.testing.assert_array_equal(split, repeat.elevation)
    permutation = np.random.default_rng(22).permutation(len(positions))
    reordered = np.empty_like(repeat.elevation)
    reordered[permutation] = field.sample(positions[permutation]).elevation
    np.testing.assert_array_equal(reordered, repeat.elevation)

    unvaried = SourceCoastalField(
        sample_continental_weight=field.sample_continental_weight,
        sample_density_anomaly=field.sample_density_anomaly,
        influence_span_noise_seeds=field.influence_span_noise_seeds,
        sample_continental_weight_with_gradient=(
            field.sample_continental_weight_with_gradient
        ),
        sample_density_anomaly_with_gradient=(
            field.sample_density_anomaly_with_gradient
        ),
        config=SourceCoastalConfig(
            inland=SourceCoastalSpanConfig(0.2, 0.0, 1.1),
            shelf=SourceCoastalSpanConfig(0.15, 0.0, 1.1),
            slope=SourceCoastalSpanConfig(0.25, 0.0, 1.1),
            interior_height_percent=10.0,
            shelf_depth_percent=3.0,
            basin_depth_percent=80.0,
            continental_buoyancy_percent=20.0,
            oceanic_buoyancy_percent=40.0,
        ),
    )
    assert np.any(repeat.elevation != unvaried.sample(positions).elevation)


def test_inland_span_noise_only_changes_the_inland_transition():
    positions = np.array(
        [
            [0.0, -0.3, 0.1],
            [0.2, 0.4, -0.6],
            [0.4, 0.2, 0.8],
            [0.6, 0.30699166298440383, 0.4884871577873784],
            [0.6, -0.4001305668962021, -0.019229876274990065],
        ]
    )
    base = _span_noise_field().sample(positions).elevation
    varied = _span_noise_field(inland_strength=0.75).sample(positions).elevation
    inland_multipliers = noise_multiplier(
        positions[3:], seed=41, frequency=1.0, strength=0.75
    )

    assert inland_multipliers[0] < 0.5 < inland_multipliers[1]
    np.testing.assert_array_equal(varied[:3], base[:3])
    np.testing.assert_allclose(base[3:], [0.05, 0.05], atol=1e-15)
    np.testing.assert_allclose(varied[3], 0.1, atol=1e-15)
    assert varied[4] < base[4]


def test_shelf_span_noise_moves_shelf_break_and_slope_start_not_coastline():
    positions = np.array(
        [
            [0.1, -0.8316788529999601, -0.8864552193257649],
            [0.1, 0.7395405514394944, -0.9550235817083095],
            [0.4, 0.12, 0.25],
            [0.8, 0.2, 0.4],
        ]
    )
    base = _span_noise_field().sample(positions).elevation
    varied = _span_noise_field(shelf_strength=0.75).sample(positions).elevation
    shelf_multipliers = noise_multiplier(
        positions[:2], seed=43, frequency=1.0, strength=0.75
    )

    assert shelf_multipliers[0] < 1.0 < shelf_multipliers[1]
    np.testing.assert_allclose(base[:2], [-0.03, -0.03], atol=1e-15)
    assert varied[0] < -0.03
    assert -0.03 < varied[1] < 0.0
    np.testing.assert_allclose(varied[2], 0.0, atol=1e-15)
    np.testing.assert_array_equal(varied[3], base[3])


def test_slope_span_noise_only_changes_the_transition_to_basin_depth():
    positions = np.array(
        [
            [-0.1, 0.11124678189889381, 0.6056298765135117],
            [-0.1, -0.2634336992552535, -0.09211683061575782],
            [0.2, 0.4, 0.1],
            [0.4, 0.1, 0.2],
            [0.8, 0.3, -0.3],
            [-1.0, 0.1, 0.2],
        ]
    )
    base = _span_noise_field().sample(positions).elevation
    varied = _span_noise_field(slope_strength=0.75).sample(positions).elevation
    slope_multipliers = noise_multiplier(
        positions[:2], seed=47, frequency=1.0, strength=0.75
    )
    transition_ratio = (0.7 - 0.45 - 0.15) / 0.25

    assert slope_multipliers[0] < transition_ratio < slope_multipliers[1]
    np.testing.assert_allclose(varied[0], -0.8, atol=1e-15)
    assert -0.8 < varied[1] < -0.03
    np.testing.assert_array_equal(varied[2:], base[2:])


def test_source_coastal_field_returns_typed_empty_arrays_without_sampling():
    def unexpected_sample(_positions):
        raise AssertionError("empty query must not sample a component")

    field = SourceCoastalField(
        unexpected_sample,
        unexpected_sample,
        influence_span_noise_seeds=(1, 2, 3),
        sample_continental_weight_with_gradient=_zero_gradient(unexpected_sample),
        sample_density_anomaly_with_gradient=_zero_gradient(unexpected_sample),
    )
    sample = field.sample(np.empty((0, 3)))

    assert sample.continental_weight.shape == sample.elevation.shape == (0,)
    assert sample.continental_weight.dtype == sample.elevation.dtype == np.float64
    assert not sample.continental_weight.flags.writeable
    assert not sample.elevation.flags.writeable


def test_coastal_profile_partials_match_finite_differences_across_segments():
    margins = np.array([0.25, 0.15, 0.075, 0.0, -0.125, -0.3])
    parameters = {
        "inland_width": np.full(len(margins), 0.2),
        "shelf_width": np.full(len(margins), 0.15),
        "slope_width": np.full(len(margins), 0.25),
        "interior_height": np.full(len(margins), 0.01),
        "shelf_depth": np.full(len(margins), 0.003),
        "basin_depth": np.full(len(margins), 0.06),
    }
    partials = coastal_height_profile_with_partials(margins, **parameters)
    np.testing.assert_array_equal(partials[0][[1, 3]], np.array([0.0, -0.003]))

    interior_indices = np.array([0, 2, 4])
    epsilon = 1e-6
    inputs = {"margin_distance": margins, **parameters}
    for partial_index, name in enumerate(inputs, start=1):
        plus = {key: value.copy() for key, value in inputs.items()}
        minus = {key: value.copy() for key, value in inputs.items()}
        plus[name] += epsilon
        minus[name] -= epsilon
        plus_value = coastal_height_profile(plus.pop("margin_distance"), **plus)
        minus_value = coastal_height_profile(minus.pop("margin_distance"), **minus)
        finite_difference = (plus_value - minus_value) / (2.0 * epsilon)
        np.testing.assert_allclose(
            partials[partial_index][interior_indices],
            finite_difference[interior_indices],
            rtol=1e-6,
            atol=1e-8,
        )
