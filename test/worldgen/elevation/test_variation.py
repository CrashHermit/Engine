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


def test_variation_controls_preserve_geology_and_other_elevation_components():
    from src.worldgen.config import WorldgenConfig
    from src.worldgen.generate import generate_world

    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    zero_config = replace(
        config,
        elevation=replace(
            config.elevation,
            variation=replace(config.elevation.variation, amplitude_percent=0.0),
        ),
    )
    variation_config = replace(config.elevation.variation, amplitude_percent=0.003)
    varied_config = replace(
        config,
        elevation=replace(config.elevation, variation=variation_config),
    )
    zero = generate_world(zero_config)
    varied = generate_world(varied_config)

    np.testing.assert_array_equal(zero.geology.plate_ids, varied.geology.plate_ids)
    np.testing.assert_array_equal(
        zero.geology.crust.region_ids, varied.geology.crust.region_ids
    )
    np.testing.assert_array_equal(
        zero.geology.crust.continental_mask,
        varied.geology.crust.continental_mask,
    )
    np.testing.assert_array_equal(
        zero.geology.boundary_edge_indices,
        varied.geology.boundary_edge_indices,
    )
    for name in (
        "coastal_elevation",
        "tectonic_relief",
        "volcanic_relief",
        "impact_relief",
        "margin_distance",
        "coastal_elevation_range_m",
    ):
        np.testing.assert_array_equal(
            getattr(zero.elevation, name), getattr(varied.elevation, name)
        )

    amplitude_m = variation_config.amplitude_percent * zero.radius_m / 100.0
    np.testing.assert_allclose(
        varied.elevation.elevation - zero.elevation.elevation,
        varied.elevation.terrain_variation,
        rtol=0.0,
        atol=1e-10,
    )
    assert np.max(np.abs(varied.elevation.terrain_variation)) <= amplitude_m
    mask = varied.geology.crust.continental_mask
    assert np.ptp(varied.elevation.terrain_variation[mask]) > 0.0
    assert np.ptp(varied.elevation.terrain_variation[~mask]) > 0.0
    variation_fraction = variation_config.amplitude_percent / 100.0
    np.testing.assert_array_equal(
        varied.elevation_field.elevation_range_fraction,
        (
            zero.elevation_field.elevation_range_fraction[0] - variation_fraction,
            zero.elevation_field.elevation_range_fraction[1] + variation_fraction,
        ),
    )
    np.testing.assert_array_equal(
        varied.elevation_field.coastal_elevation_range_fraction,
        zero.elevation_field.coastal_elevation_range_fraction,
    )
    assert varied.elevation.elevation.min() >= varied.elevation.elevation_range_m[0]
    assert varied.elevation.elevation.max() <= varied.elevation.elevation_range_m[1]
