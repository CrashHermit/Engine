from dataclasses import replace

import numpy as np

from src.worldgen.config import PlanetConfig, WorldgenConfig
from src.worldgen.elevation.config import ImpactConfig
from src.worldgen.elevation.impact import ImpactField, generate_impact_field
from src.worldgen.generate import generate_world
from src.worldgen.render.layers import LAYERS, elevation_colormap, layer_style
from src.worldgen.surface import SurfaceResult


def test_elevation_layers_anchor_sea_level_and_accept_fixed_range() -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    default = layer_style(world, "elevation")
    coastal = layer_style(world, "coastal-elevation")

    for style in (default, coastal):
        zero_fraction = (0.0 - style.clim[0]) / (style.clim[1] - style.clim[0])
        np.testing.assert_allclose(
            style.cmap(zero_fraction)[:3],
            np.array([244, 241, 220]) / 255,
            atol=0.01,
        )

    fixed = layer_style(world, "elevation", (-12_000.0, 8_000.0))
    assert fixed.clim == (-12_000.0, 8_000.0)
    fixed_map = elevation_colormap(fixed.clim)
    np.testing.assert_allclose(
        fixed_map(0.6)[:3], np.array([244, 241, 220]) / 255, atol=0.01
    )


def test_elevation_colormap_has_bathymetry_and_hypsometric_steps() -> None:
    cmap = elevation_colormap((-12_000.0, 8_000.0))

    deep_ocean = np.asarray(cmap(0.1)[:3])
    shallow_ocean = np.asarray(cmap(0.45)[:3])
    lowland = np.asarray(cmap(0.66)[:3])
    highland = np.asarray(cmap(0.88)[:3])
    summit = np.asarray(cmap(0.99)[:3])

    assert deep_ocean[2] > deep_ocean[0]
    assert shallow_ocean[1] > shallow_ocean[0]
    assert lowland[1] > lowland[0]
    assert highland[0] > highland[2]
    assert np.all(summit > 0.8)


def test_terrain_variation_layer_uses_configured_symmetric_range() -> None:
    variation = replace(WorldgenConfig().elevation.variation, amplitude_percent=0.01)
    config = WorldgenConfig(
        seed=17,
        subdivision_frequency=2,
        elevation=replace(WorldgenConfig().elevation, variation=variation),
        planet=PlanetConfig(radius_m=1_000_000.0),
    )
    world = generate_world(config)
    style = layer_style(world, "terrain-variation", (-12_000.0, 8_000.0))

    assert "terrain-variation" in LAYERS
    assert "elevation" in LAYERS
    assert style.title == "Terrain variation (m)"
    assert style.cmap == "coolwarm"
    assert style.clim == (-100.0, 100.0)
    np.testing.assert_array_equal(style.values, world.elevation.terrain_variation)
    assert np.max(np.abs(style.values)) <= 100.0
    disabled_variation = replace(variation, amplitude_percent=0.0)
    disabled_world = generate_world(
        replace(
            config,
            elevation=replace(config.elevation, variation=disabled_variation),
        )
    )
    disabled_style = layer_style(disabled_world, "terrain-variation")
    assert disabled_style.clim == (-1.0, 1.0)
    assert np.count_nonzero(disabled_style.values) == 0


def test_impact_relief_layer_uses_signed_values_and_query_independent_bounds():
    elevation = replace(
        WorldgenConfig().elevation,
        impacts=ImpactConfig(count=0),
    )
    world = generate_world(
        WorldgenConfig(
            seed=17,
            subdivision_frequency=2,
            planet=PlanetConfig(radius_m=1_000_000.0),
            elevation=elevation,
        )
    )
    config = ImpactConfig(count=1)
    radius_percent = 1.0
    theta = radius_percent * 2.0 * np.pi / 100.0
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [np.cos(theta), np.sin(theta), 0.0],
            [-1.0, 0.0, 0.0],
        ]
    )
    impacts = ImpactField(
        config=config,
        centers=np.array([[1.0, 0.0, 0.0]]),
        radii_percent=np.array([radius_percent]),
        depths_percent=np.array([0.01]),
        sharpnesses=np.array([1.0]),
    )
    field = replace(world.elevation_field, impacts=impacts)
    sampled_world = replace(
        world,
        elevation_field=field,
        elevation=field.sample(positions),
    )
    style = layer_style(sampled_world, "impact-relief")

    assert "impact-relief" in LAYERS
    assert style.title == "Impact relief (m)"
    assert style.cmap == "coolwarm"
    assert style.clim == (-100.0, 100.0)
    np.testing.assert_allclose(style.values, [-100.0, 25.0, 0.0], atol=1e-8)

    subset_world = replace(
        sampled_world,
        elevation=field.sample(positions[:1]),
    )
    assert layer_style(subset_world, "impact-relief").clim == style.clim

    empty_impacts = generate_impact_field(
        ImpactConfig(count=0), rng=np.random.default_rng(1)
    )
    empty_field = replace(field, impacts=empty_impacts)
    empty_world = replace(
        sampled_world,
        elevation_field=empty_field,
        elevation=empty_field.sample(positions),
    )
    assert layer_style(empty_world, "impact-relief").clim == (-1.0, 1.0)


def test_surface_layers_show_distinct_metrics_and_ignore_elevation_override() -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    count = len(world.mesh.vertices)
    land_height = np.zeros(count)
    water_depth = np.zeros(count)
    slope_degrees = np.zeros(count)
    local_relief = np.zeros(count)
    roughness = np.zeros(count)
    water_depth[0] = 4_300.0
    land_height[1] = 320.0
    slope_degrees[0] = 12.0
    slope_degrees[2] = 65.0
    land_height[2] = 1_800.0
    local_relief[2] = 2_500.0
    roughness[2] = 650.0
    surface = SurfaceResult(
        land_height=land_height,
        water_depth=water_depth,
        slope_degrees=slope_degrees,
        local_relief=local_relief,
        roughness=roughness,
    )
    diagnostic_world = replace(world, surface=surface)
    expected = {
        "land-height": (land_height, "Land height (m)", "YlOrBr", (0.0, 1_800.0)),
        "water-depth": (
            water_depth,
            "Water depth below sea level (m)",
            "Blues",
            (0.0, 4_300.0),
        ),
        "slope": (slope_degrees, "Surface slope (degrees)", "magma", (0.0, 90.0)),
        "local-relief": (
            local_relief,
            "Local relief (m)",
            "viridis",
            (0.0, 2_500.0),
        ),
        "roughness": (
            roughness,
            "Detrended roughness (m RMS)",
            "inferno",
            (0.0, 650.0),
        ),
    }

    for name, (values, title, cmap, clim) in expected.items():
        assert name in LAYERS
        style = layer_style(diagnostic_world, name, (-10_000.0, 10_000.0))
        assert style.title == title
        assert style.cmap == cmap
        assert style.clim == clim
        np.testing.assert_array_equal(style.values, values)

    assert layer_style(diagnostic_world, "water-depth").values[0] > 0.0
    assert layer_style(diagnostic_world, "land-height").values[1] > 0.0
    assert layer_style(diagnostic_world, "slope").values[2] > 0.0
    assert layer_style(diagnostic_world, "local-relief").values[2] > 0.0
    assert layer_style(diagnostic_world, "roughness").values[2] > 0.0


def test_surface_layer_ranges_cover_all_zero_and_empty_samples() -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    fields = (
        "land_height",
        "water_depth",
        "slope_degrees",
        "local_relief",
        "roughness",
    )
    zero_surface = replace(
        world.surface,
        **{name: np.zeros(len(world.mesh.vertices)) for name in fields},
    )
    empty_surface = replace(world.surface, **{name: np.empty(0) for name in fields})

    for candidate in (
        replace(world, surface=zero_surface),
        replace(world, surface=empty_surface),
    ):
        for layer in ("land-height", "water-depth", "local-relief", "roughness"):
            assert layer_style(candidate, layer).clim == (0.0, 1.0)
        assert layer_style(candidate, "slope").clim == (0.0, 90.0)
