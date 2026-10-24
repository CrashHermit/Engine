from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field
from src.worldgen.relief.config import ReliefConfig
from src.worldgen.relief.volcanism import VolcanicField, VolcanismConfig


def _field(seed=123, *, unwarped=False, **settings):
    config = replace(VolcanismConfig(), **settings)
    world_config = replace(
        WorldgenConfig(seed=seed),
        relief=replace(
            ReliefConfig(),
            volcanism=replace(config, hotspot_count=0, tectonic_count=0),
        ),
    )
    if unwarped:
        world_config = replace(
            world_config, warp=replace(world_config.warp, amplitude=0.0)
        )
    geology = generate_world_field(world_config).geology
    return VolcanicField(
        sample_relief_inputs=geology.sample_relief_inputs,
        sample_relief_inputs_with_gradient=geology.sample_relief_inputs_with_gradient,
        noise_seed=seed + 71,
        warp=geology.regions.warp,
        config=config,
    ), geology


def _rod_arrays(rod):
    return tuple(
        getattr(rod, name) for name in ("directions", "widths", "lengths", "heights")
    )


def test_weighted_rod_populations_are_seeded_and_independent():
    field, _ = _field(candidate_count=128, hotspot_count=8, tectonic_count=7)
    same, _ = _field(candidate_count=128, hotspot_count=8, tectonic_count=7)
    different, _ = _field(124, candidate_count=128, hotspot_count=8, tectonic_count=7)
    for name in ("hotspots", "tectonic_rods"):
        for first, second in zip(
            _rod_arrays(getattr(field, name)), _rod_arrays(getattr(same, name))
        ):
            np.testing.assert_array_equal(first, second)
    assert not np.array_equal(field.hotspots.directions, different.hotspots.directions)

    no_hotspots, _ = _field(candidate_count=128, hotspot_count=0, tectonic_count=7)
    no_tectonic, _ = _field(candidate_count=128, hotspot_count=8, tectonic_count=0)
    for first, second in zip(
        _rod_arrays(field.tectonic_rods), _rod_arrays(no_hotspots.tectonic_rods)
    ):
        np.testing.assert_array_equal(first, second)
    for first, second in zip(
        _rod_arrays(field.hotspots), _rod_arrays(no_tectonic.hotspots)
    ):
        np.testing.assert_array_equal(first, second)


def test_independent_suitability_values_and_analytic_gradients():
    field, _ = _field(
        unwarped=True, candidate_count=128, hotspot_count=4, tectonic_count=4
    )
    # Isolate the geological rule from float32 warp quantization.
    points = field.tectonic_rods.directions[:2]
    sampled = field.tectonic_suitability_with_gradient(points)
    step = 1e-6
    expected = np.column_stack(
        [
            (
                field.tectonic_suitability(points + axis * step)
                - field.tectonic_suitability(points - axis * step)
            )
            / (2 * step)
            for axis in np.eye(3)
        ]
    )
    assert np.all(sampled.values > 0)
    np.testing.assert_allclose(
        sampled.values, field.tectonic_suitability(points), atol=1e-12
    )
    np.testing.assert_allclose(sampled.gradients, expected, rtol=1e-5, atol=1e-7)
    points = np.array([[0.41, -0.12, 0.73], [-0.32, 0.54, 0.26]])
    sampled = field.hotspot_suitability_with_gradient(points)
    step = 4e-4
    expected = np.column_stack(
        [
            (
                field.hotspot_suitability(points + axis * step)
                - field.hotspot_suitability(points - axis * step)
            )
            / (2 * step)
            for axis in np.eye(3)
        ]
    )
    # Native octave offsets quantize coordinates; compare the whole derivative,
    # not relative errors of near-cancelling individual components.
    np.testing.assert_allclose(
        sampled.values, field.hotspot_suitability(points), atol=1e-12
    )
    assert np.linalg.norm(sampled.gradients - expected) < 0.03 * np.linalg.norm(
        sampled.gradients
    )


def test_unwarped_hotspot_has_radial_profile_and_analytic_world_gradient():
    field, _ = _field(
        candidate_count=128,
        hotspot_count=1,
        tectonic_count=0,
        hotspot_width_min_percent=20.0,
        hotspot_width_max_percent=20.0,
        hotspot_amplitude_min=0.8,
        hotspot_amplitude_max=0.8,
    )
    rod = field.hotspots
    direction = rod.directions[0]
    tangent = np.cross(direction, [0.0, 0.0, 1.0])
    if np.linalg.norm(tangent) < 1e-8:
        tangent = np.cross(direction, [0.0, 1.0, 0.0])
    tangent /= np.linalg.norm(tangent)
    center = direction * 0.5
    offset = rod.widths[0] * 0.25
    points = np.stack((center, center + offset * tangent, center - offset * tangent))
    sampled = rod.sample_with_gradient(points)
    radial_base = 1.0 - (offset / rod.widths[0]) ** 2
    expected = rod.heights[0] * radial_base**rod.profile_power
    np.testing.assert_allclose(sampled.values[1:], expected, rtol=1e-12, atol=1e-12)
    assert sampled.values[0] > sampled.values[1]
    expected_gradient = (
        -2.0
        * rod.profile_power
        * rod.heights[0]
        * offset
        / rod.widths[0] ** 2
        * radial_base ** (rod.profile_power - 1.0)
    )
    np.testing.assert_allclose(
        sampled.gradients[1] @ tangent, expected_gradient, rtol=1e-12, atol=1e-12
    )
    np.testing.assert_allclose(
        sampled.gradients[2] @ tangent, -expected_gradient, rtol=1e-12, atol=1e-12
    )


def test_rod_relief_is_world_coordinate_sampled_and_radius_scaled():
    field, _ = _field(candidate_count=128, hotspot_count=6, tectonic_count=6)
    points = field.hotspots.directions[:1] * (field.hotspots.lengths[:1] * 0.5)
    sample = field.sample(points)
    doubled, _ = _field(
        candidate_count=128,
        hotspot_count=6,
        tectonic_count=6,
        relief_height_percent=0.0094,
    )
    np.testing.assert_array_equal(sample.strength, doubled.sample(points).strength)
    np.testing.assert_array_equal(sample.relief * 2.0, doubled.sample(points).relief)
    assert sample.strength[0] > 0.0
    assert not sample.relief.flags.writeable


def test_empty_samples_and_intraplate_diagnostics():
    field, _ = _field(candidate_count=64, hotspot_count=3, tectonic_count=3)
    empty = field.sample(np.empty((0, 3)))
    assert empty.relief.shape == (0,)
    assert not empty.relief.flags.writeable
    diagnostic = field.sample_intraplate(field.hotspots.directions[:1] * 0.5)
    assert diagnostic[0] > 0.0
    assert not diagnostic.flags.writeable
