from dataclasses import replace

import numpy as np

from src.worldgen.relief.impact import (
    ImpactConfig,
    ImpactField,
    generate_impact_field,
    impact_profile,
    impact_profile_with_partials,
)


def _field(count=1):
    return ImpactField(
        np.tile([0.0, 0.0, 1.0], (count, 1)),
        np.full(count, 0.2),
        np.full(count, 0.01),
        np.full(count, 0.002),
        np.full(count, 1.8),
        ImpactConfig(count=count),
    )


def test_crater_center_rim_joins_and_outer_support():
    b = 0.75**2
    q = np.array([0.0, b * 0.5, b, (b + 1.0) / 2, 1.0, 1.1])
    values = impact_profile(
        q, radius=1.0, depth=0.1, rim_height=0.03, rim_width_fraction=0.25
    )
    np.testing.assert_allclose(values, [-0.1, -0.0125, 0.0, 0.03, 0.0, 0.0], atol=1e-15)
    partials = impact_profile_with_partials(
        q, radius=1.0, depth=0.1, rim_height=0.03, rim_width_fraction=0.25
    )
    np.testing.assert_allclose(partials[0], values, atol=1e-15)
    np.testing.assert_array_equal(partials[1][[2, 4, 5]], np.zeros(3))


def test_rod_support_is_one_sided_finite_and_rotationally_symmetric():
    field = _field()
    points = np.array(
        [
            [0, 0, 1],
            [0.1, 0, 1],
            [0, 0.1, 1],
            [0.21, 0, 1],
            [0, 0, -1],
            [0, 0, 0],
            [0, 0, 1.8],
        ]
    )
    values = field.sample(points)
    assert values[0] == -0.01
    assert values[1] == values[2] < 0.0
    np.testing.assert_array_equal(values[3:], np.zeros(4))
    np.testing.assert_array_equal(
        field.sample_with_gradient(points[:1]).gradients, [[0, 0, 0]]
    )


def test_overlapping_impacts_add_instead_of_selecting_a_winner():
    points = np.array([[0, 0, 1], [0.1, 0, 1], [0.18, 0, 1]])
    np.testing.assert_allclose(
        _field(2).sample(points), 2 * _field().sample(points), atol=1e-15
    )
    np.testing.assert_allclose(
        _field(2).sample_with_gradient(points).gradients,
        2 * _field().sample_with_gradient(points).gradients,
        atol=1e-15,
    )


def test_impact_gradients_cover_bowl_rim_axial_tapers_and_cutoffs():
    field = _field()
    points = np.array(
        [
            [0, 0, 1],
            [0.05, 0.03, 1],
            [0.18, 0, 1],
            [0.2, 0, 1],
            [0.1, 0, 0.09],
            [0.1, 0, 1.71],
            [0, 0, 1.8],
        ]
    )
    sample = field.sample_with_gradient(points)
    np.testing.assert_allclose(sample.values, field.sample(points), atol=1e-15)
    step = 1e-6
    finite = np.column_stack(
        [
            (field.sample(points + step * axis) - field.sample(points - step * axis))
            / (2 * step)
            for axis in np.eye(3)
        ]
    )
    # Axial smoothstep joins are C1: extrapolate the O(step) endpoint error.
    half_step = np.column_stack(
        [
            (
                field.sample(points + step * axis / 2)
                - field.sample(points - step * axis / 2)
            )
            / step
            for axis in np.eye(3)
        ]
    )
    finite = 2 * half_step - finite
    np.testing.assert_allclose(sample.gradients, finite, rtol=2e-6, atol=2e-8)


def test_profile_parameter_partials_match_actual_shape_changes():
    q = np.array([0.0, 0.005, 0.032, 0.05])
    parameters = dict(radius=0.2, depth=0.01, rim_height=0.002, rim_width_fraction=0.25)
    partials = impact_profile_with_partials(q, **parameters)
    step = 1e-7
    numerical_q = (
        impact_profile(q + step, **parameters) - impact_profile(q - step, **parameters)
    ) / (2 * step)
    np.testing.assert_allclose(partials[1], numerical_q, rtol=1e-6, atol=1e-8)
    for index, name in enumerate(("radius", "depth", "rim_height"), start=2):
        upper = dict(parameters, **{name: parameters[name] + step})
        lower = dict(parameters, **{name: parameters[name] - step})
        finite = (impact_profile(q, **upper) - impact_profile(q, **lower)) / (2 * step)
        np.testing.assert_allclose(partials[index], finite, rtol=1e-6, atol=1e-8)


def test_placement_is_deterministic_batch_independent_and_zero_count_disables_it():
    config = ImpactConfig(count=3)
    field = generate_impact_field(config, seed=91)
    repeat = generate_impact_field(config, seed=91)
    for name in ("directions", "radii", "depths", "rim_heights", "lengths"):
        np.testing.assert_array_equal(getattr(field, name), getattr(repeat, name))
        assert not getattr(field, name).flags.writeable
    points = np.concatenate([field.directions, field.directions + 0.01])
    values = field.sample(points)
    order = np.array([4, 1, 3, 0, 5, 2])
    np.testing.assert_array_equal(field.sample(points[order]), values[order])
    empty = generate_impact_field(replace(config, count=0), seed=91)
    np.testing.assert_array_equal(empty.sample(points), np.zeros(len(points)))
    np.testing.assert_array_equal(
        empty.sample_with_gradient(points).gradients, np.zeros_like(points)
    )
