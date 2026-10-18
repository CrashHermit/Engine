from dataclasses import replace

import numpy as np

from src.worldgen.config import PlanetConfig, WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.geometry import generate_icosphere
from src.worldgen.elevation.config import CoastalConfig, CoastalWidthConfig
from src.worldgen.elevation.coastal import coastal_profile, _sample_width


def test_smooth_coastal_profile_saturates_at_expected_heights() -> None:
    config = CoastalConfig()
    distances = np.array(
        [
            config.shelf.base_percent + config.inland.base_percent,
            config.shelf.base_percent,
            0.0,
            -(config.shelf.base_percent + config.slope.base_percent),
            -(2 * config.shelf.base_percent + config.slope.base_percent),
        ]
    )
    anomaly = np.zeros(5)
    np.testing.assert_allclose(
        coastal_profile(
            distances,
            config,
            100.0,
            density_anomaly=anomaly,
            inland_width=np.full(5, config.inland.base_percent),
            shelf_width=np.full(5, config.shelf.base_percent),
            slope_width=np.full(5, config.slope.base_percent),
        ),
        [
            config.interior_height_percent,
            0.0,
            -config.shelf_depth_percent,
            -config.basin_depth_percent,
            -config.basin_depth_percent,
        ],
    )


def test_density_buoyancy_changes_saturated_targets_not_coasts():
    config = CoastalConfig()
    distances = np.array([10.0, -10.0, 1.0, 0.0])
    anomaly = np.array([-0.2, 0.2, 0.2, -0.2])
    widths = np.ones(4)
    result = coastal_profile(
        distances,
        config,
        100.0,
        density_anomaly=anomaly,
        inland_width=widths,
        shelf_width=widths,
        slope_width=widths,
    )
    assert result[0] > config.interior_height_percent
    assert result[1] < -config.basin_depth_percent
    # At the coast and shelf break, profile blending remains fixed.
    assert result[2] == 0.0
    np.testing.assert_allclose(result[3], -config.shelf_depth_percent)
    opposite = coastal_profile(
        distances,
        config,
        100.0,
        density_anomaly=-anomaly,
        inland_width=widths,
        shelf_width=widths,
        slope_width=widths,
    )
    assert opposite[0] < config.interior_height_percent
    assert opposite[1] > -config.basin_depth_percent
    np.testing.assert_array_equal(opposite[2:], result[2:])


def test_zero_buoyancy_responses_preserve_baseline_profile():
    config = CoastalConfig()
    from dataclasses import replace
    from src.worldgen.elevation.config import BuoyancyConfig

    config = replace(config, buoyancy=BuoyancyConfig(0.0, 0.0))
    distances = np.array([5.0, 0.0, -5.0])
    widths = np.ones(3)
    base = coastal_profile(
        distances,
        config,
        100.0,
        density_anomaly=np.zeros(3),
        inland_width=widths,
        shelf_width=widths,
        slope_width=widths,
    )
    varied = coastal_profile(
        distances,
        config,
        100.0,
        density_anomaly=np.array([-1.0, 0.0, 1.0]),
        inland_width=widths,
        shelf_width=widths,
        slope_width=widths,
    )
    np.testing.assert_array_equal(base, varied)


def test_margin_distances_have_class_signs() -> None:
    world = generate_world(WorldgenConfig(seed=3, subdivision_frequency=2))
    mask = world.geology.crust.continental_mask
    terrain = world.elevation
    assert np.all(terrain.margin_distance[mask] > 0)
    assert np.all(terrain.margin_distance[~mask] < 0)
    assert not terrain.margin_distance.flags.writeable
    assert not terrain.coastal_elevation.flags.writeable
    assert not terrain.tectonic_relief.flags.writeable
    assert not terrain.elevation.flags.writeable
    assert not terrain.volcanic_relief.flags.writeable
    assert not terrain.terrain_variation.flags.writeable
    assert not terrain.impact_relief.flags.writeable
    assert not terrain.crust_boundary_edge_indices.flags.writeable


def test_world_terrain_is_deterministic_and_uses_crust_mask() -> None:
    config = WorldgenConfig(seed=123, subdivision_frequency=3)
    first, second = generate_world(config), generate_world(config)

    np.testing.assert_array_equal(
        first.elevation.margin_distance,
        second.elevation.margin_distance,
    )
    np.testing.assert_array_equal(
        first.elevation.coastal_elevation,
        second.elevation.coastal_elevation,
    )
    np.testing.assert_array_equal(
        first.elevation.terrain_variation,
        second.elevation.terrain_variation,
    )
    np.testing.assert_array_equal(
        first.elevation.impact_relief,
        second.elevation.impact_relief,
    )
    np.testing.assert_array_equal(
        first.elevation.crust_boundary_edge_indices,
        np.flatnonzero(
            first.geology.crust.continental_mask[first.mesh.edges[:, 0]]
            != first.geology.crust.continental_mask[first.mesh.edges[:, 1]]
        ),
    )
    np.testing.assert_array_equal(
        first.geology.crust.continental_mask,
        second.geology.crust.continental_mask,
    )


def test_radius_scales_elevation_without_changing_geography() -> None:
    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    first = generate_world(config)
    larger = generate_world(
        replace(config, planet=PlanetConfig(radius_m=config.planet.radius_m * 2.0))
    )

    np.testing.assert_array_equal(first.mesh.vertices, larger.mesh.vertices)
    np.testing.assert_array_equal(first.geology.plate_ids, larger.geology.plate_ids)
    np.testing.assert_array_equal(
        first.geology.crust.region_ids, larger.geology.crust.region_ids
    )
    np.testing.assert_array_equal(
        first.elevation.margin_distance,
        larger.elevation.margin_distance,
    )
    np.testing.assert_allclose(
        larger.elevation.coastal_elevation,
        first.elevation.coastal_elevation * 2.0,
    )
    np.testing.assert_allclose(
        larger.elevation.volcanic_relief,
        first.elevation.volcanic_relief * 2.0,
    )
    np.testing.assert_allclose(
        larger.elevation.terrain_variation,
        first.elevation.terrain_variation * 2.0,
    )
    np.testing.assert_allclose(
        larger.elevation.impact_relief,
        first.elevation.impact_relief * 2.0,
    )


def test_default_reference_world_has_earth_scale_relief() -> None:
    positions, _ = generate_icosphere(80)
    ranges = []
    for seed in (123, 2026, 31415):
        world = generate_world(WorldgenConfig(seed=seed, subdivision_frequency=40))
        sampled = world.elevation_field.sample(positions).elevation
        ranges.append((float(sampled.min()), float(sampled.max())))

    minima, maxima = np.asarray(ranges).T
    assert np.all((minima > -11_500.0) & (minima < -9_500.0))
    assert np.all((maxima > 8_500.0) & (maxima < 9_500.0))


def test_width_samples_are_stable_when_sampling_more_positions() -> None:
    positions, _ = generate_icosphere(3)
    config = CoastalWidthConfig(base_percent=1.25, variation_strength=0.6)
    whole = _sample_width(positions, config, noise_seed=42)
    subset = _sample_width(positions[::3], config, noise_seed=42)
    np.testing.assert_array_equal(subset, whole[::3])
    assert np.all(whole >= 0.5)
    assert np.all(whole <= 2.0)
    uniform = _sample_width(
        positions, replace(config, variation_strength=0.0), noise_seed=42
    )
    np.testing.assert_array_equal(uniform, np.full(len(positions), 1.25))
