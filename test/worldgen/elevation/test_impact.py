from dataclasses import replace

import numpy as np

from src.worldgen.elevation.config import ImpactConfig
from src.worldgen.elevation.impact import ImpactField, generate_impact_field
from src.worldgen.elevation.profiles import impact_profile


def _single_impact(
    *,
    center=(1.0, 0.0, 0.0),
    radius_percent=1.0,
    depth_percent=0.01,
    sharpness=1.0,
    rim_height_fraction=0.25,
    ejecta_width_fraction=1.0,
):
    config = ImpactConfig(
        count=1,
        rim_height_fraction=rim_height_fraction,
        ejecta_width_fraction=ejecta_width_fraction,
    )
    return ImpactField(
        config=config,
        centers=np.array([center], dtype=np.float64),
        radii_percent=np.array([radius_percent], dtype=np.float64),
        depths_percent=np.array([depth_percent], dtype=np.float64),
        sharpnesses=np.array([sharpness], dtype=np.float64),
    )


def _radial_points(center, radius_percent, q_values):
    theta = np.asarray(q_values) * radius_percent * 2.0 * np.pi / 100.0
    center = np.asarray(center, dtype=np.float64)
    tangent = np.cross(center, np.array([0.0, 0.0, 1.0]))
    if np.linalg.norm(tangent) < 1e-12:
        tangent = np.cross(center, np.array([0.0, 1.0, 0.0]))
    tangent /= np.linalg.norm(tangent)
    points = center[None, :] * np.cos(theta)[:, None]
    points += tangent[None, :] * np.sin(theta)[:, None]
    return points


def test_crater_bowl_rim_and_apron_have_expected_spherical_heights():
    field = _single_impact()
    q = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.1])
    points = _radial_points(field.centers[0], 1.0, q)

    values = field.sample(points, radius_m=1_000_000.0)

    np.testing.assert_allclose(values, [-100.0, -37.5, 25.0, 12.5, 0.0, 0.0])
    np.testing.assert_allclose(field.bounds(1_000_000.0), (-100.0, 25.0))


def test_crater_profile_is_continuous_at_rim_and_apron_support():
    field = _single_impact()
    epsilon = 1e-7
    q = np.array([1.0 - epsilon, 1.0 + epsilon, 2.0 - epsilon, 2.0 + epsilon])
    points = _radial_points(field.centers[0], 1.0, q)

    values = field.sample(points, radius_m=1_000_000.0)

    np.testing.assert_allclose(values[:2], [25.0, 25.0], atol=1e-8)
    np.testing.assert_allclose(values[2:], [0.0, 0.0], atol=1e-8)


def test_impact_distance_is_spherical_around_poles_and_date_line():
    q = 0.5
    theta = q * 0.01 * 2.0 * np.pi
    cases = (
        ((1.0, 0.0, 0.0), (np.cos(theta), np.sin(theta), 0.0)),
        ((0.0, 0.0, 1.0), (0.0, np.sin(theta), np.cos(theta))),
        ((-1.0, 0.0, 0.0), (-np.cos(theta), -np.sin(theta), 0.0)),
    )

    values = [
        _single_impact(center=center).sample(np.asarray([point]), radius_m=1_000_000.0)[
            0
        ]
        for center, point in cases
    ]

    np.testing.assert_allclose(values, [-37.5] * 3, atol=1e-10)


def test_sharpness_concentrates_bowl_and_apron_without_changing_depth_or_rim():
    q = np.array([0.0, 0.5, 1.0, 1.5])
    points = _radial_points((1.0, 0.0, 0.0), 1.0, q)
    smooth = _single_impact(sharpness=1.0).sample(points, 1_000_000.0)
    sharp = _single_impact(sharpness=4.0).sample(points, 1_000_000.0)

    assert smooth[0] == sharp[0] == -100.0
    assert smooth[2] == sharp[2] == 25.0
    assert abs(sharp[1]) < abs(smooth[1])
    assert sharp[3] < smooth[3]


def test_radius_changes_spread_independently_of_depth():
    point = _radial_points((1.0, 0.0, 0.0), 1.0, [0.7])
    narrow = _single_impact(radius_percent=1.0).sample(point, 1_000_000.0)
    broad = _single_impact(radius_percent=2.0).sample(point, 1_000_000.0)

    assert narrow[0] != broad[0]
    assert narrow[0] < 0.0
    assert broad[0] < 0.0


def test_overlapping_impacts_add_bowl_and_rim_and_remain_within_bounds():
    single = _single_impact()
    config = ImpactConfig(count=2, rim_height_fraction=0.25, ejecta_width_fraction=1.0)
    doubled = ImpactField(
        config=config,
        centers=np.repeat(single.centers, 2, axis=0),
        radii_percent=np.repeat(single.radii_percent, 2),
        depths_percent=np.repeat(single.depths_percent, 2),
        sharpnesses=np.repeat(single.sharpnesses, 2),
    )
    points = _radial_points(single.centers[0], 1.0, [0.0, 1.0, 1.5, 2.0])
    values = doubled.sample(points, 1_000_000.0)
    expected = single.sample(points, 1_000_000.0) * 2.0

    np.testing.assert_array_equal(values, expected)
    low, high = doubled.bounds(1_000_000.0)
    assert low <= values.min()
    assert values.max() <= high
    np.testing.assert_allclose((low, high), (-200.0, 50.0))


def test_zero_sources_and_empty_position_queries_return_empty_relief():
    field = generate_impact_field(ImpactConfig(count=0), rng=np.random.default_rng(23))

    assert field.centers.shape == (0, 3)
    assert field.radii_percent.shape == (0,)
    assert field.sample(np.array([[1.0, 0.0, 0.0]]), 1_000_000.0).tolist() == [0.0]
    assert field.sample(np.empty((0, 3)), 1_000_000.0).shape == (0,)
    assert field.bounds(1_000_000.0) == (0.0, 0.0)
    for array in (
        field.centers,
        field.radii_percent,
        field.depths_percent,
        field.sharpnesses,
    ):
        assert not array.flags.writeable


def test_generated_sources_are_reproducible_without_mutating_global_rng():
    state_before = np.random.get_state()
    first = generate_impact_field(ImpactConfig(count=8), rng=np.random.default_rng(71))
    state_after = np.random.get_state()
    second = generate_impact_field(ImpactConfig(count=8), rng=np.random.default_rng(71))
    other = generate_impact_field(ImpactConfig(count=8), rng=np.random.default_rng(72))

    for before, after in zip(state_before, state_after):
        if isinstance(before, np.ndarray):
            np.testing.assert_array_equal(before, after)
        else:
            assert before == after
    np.testing.assert_array_equal(first.centers, second.centers)
    np.testing.assert_array_equal(first.radii_percent, second.radii_percent)
    assert not np.array_equal(first.centers, other.centers)
    for array in (
        first.centers,
        first.radii_percent,
        first.depths_percent,
        first.sharpnesses,
    ):
        assert not array.flags.writeable


def test_impact_sampling_is_invariant_to_query_order_and_batch_size():
    field = generate_impact_field(ImpactConfig(count=8), rng=np.random.default_rng(42))
    points = np.concatenate(
        (
            field.centers,
            _radial_points(field.centers[0], field.radii_percent[0], [0.5, 1.5]),
        )
    )
    full = field.sample(points, 1_000_000.0)
    order = np.array([len(points) - 1, 0, 2, 1])

    np.testing.assert_array_equal(field.sample(points[order], 1_000_000.0), full[order])
    np.testing.assert_array_equal(field.sample(points[:1], 1_000_000.0), full[:1])


def test_impact_profile_uses_compact_smoothstep_support():
    values = impact_profile(
        np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.1]),
        radius=1.0,
        sharpness=1.0,
        rim_height_fraction=0.25,
        ejecta_width_fraction=1.0,
    )

    np.testing.assert_allclose(values, [-1.0, -0.375, 0.25, 0.125, 0.0, 0.0])


def test_world_impact_component_is_independent_additive_and_radius_scaled():
    from src.worldgen.config import WorldgenConfig
    from src.worldgen.generate import generate_world

    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    no_impacts = replace(
        config,
        elevation=replace(
            config.elevation,
            impacts=replace(config.elevation.impacts, count=0),
        ),
    )
    impacted = generate_world(config)
    baseline = generate_world(no_impacts)

    np.testing.assert_array_equal(
        impacted.geology.plate_ids, baseline.geology.plate_ids
    )
    np.testing.assert_array_equal(
        impacted.geology.plate_velocity, baseline.geology.plate_velocity
    )
    np.testing.assert_array_equal(
        impacted.geology.crust.region_ids, baseline.geology.crust.region_ids
    )
    np.testing.assert_array_equal(
        impacted.geology.crust.effective_density,
        baseline.geology.crust.effective_density,
    )

    for name in (
        "coastal_elevation",
        "tectonic_relief",
        "volcanic_relief",
        "terrain_variation",
        "margin_distance",
    ):
        np.testing.assert_array_equal(
            getattr(impacted.elevation, name), getattr(baseline.elevation, name)
        )

    arbitrary = np.random.default_rng(23).normal(size=(7, 3))
    arbitrary /= np.linalg.norm(arbitrary, axis=1, keepdims=True)
    positions = np.concatenate((impacted.elevation_field.impacts.centers, arbitrary))
    sampled = impacted.elevation_field.sample(positions)
    base_sampled = baseline.elevation_field.sample(positions)
    np.testing.assert_allclose(
        sampled.elevation - base_sampled.elevation,
        sampled.impact_relief,
        rtol=0.0,
        atol=1e-9,
    )
    np.testing.assert_array_equal(
        sampled.impact_relief,
        impacted.elevation_field.impacts.sample(positions, impacted.radius_m),
    )
    assert np.any(
        sampled.impact_relief[: len(impacted.elevation_field.impacts.centers)]
    )
    assert not sampled.impact_relief.flags.writeable

    larger = generate_world(
        replace(
            config,
            planet=replace(config.planet, radius_m=impacted.radius_m * 2.0),
        )
    )
    np.testing.assert_array_equal(
        impacted.elevation_field.impacts.centers,
        larger.elevation_field.impacts.centers,
    )
    np.testing.assert_allclose(
        larger.elevation.impact_relief,
        impacted.elevation.impact_relief * 2.0,
    )
    np.testing.assert_allclose(
        larger.elevation_field.impacts.bounds(larger.radius_m),
        np.asarray(impacted.elevation_field.impacts.bounds(impacted.radius_m)) * 2.0,
    )

    coarser = generate_world(replace(config, subdivision_frequency=3))
    np.testing.assert_array_equal(
        impacted.elevation_field.impacts.centers,
        coarser.elevation_field.impacts.centers,
    )
