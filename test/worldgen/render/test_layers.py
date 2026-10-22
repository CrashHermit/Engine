from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.render.layers import elevation_colormap, layer_style
from src.worldgen.surface import SurfaceResult
from src.worldgen.world import WorldSample


def _sample(world):
    return WorldSample(geology=world.geology, elevation=world.elevation)


def test_public_layers_and_meter_elevation_styles():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    sample = _sample(world)

    default = layer_style(sample, "elevation", radius_m=world.radius_m)
    coastal = layer_style(sample, "coastal-elevation", radius_m=world.radius_m)
    elevation_m = sample.elevation.elevation * world.radius_m
    coastal_m = sample.elevation.coastal_elevation * world.radius_m
    for style, values in ((default, elevation_m), (coastal, coastal_m)):
        assert style.values.dtype == np.float64
        assert np.isfinite(style.values).all()
        assert style.clim[0] <= min(0.0, values.min())
        assert style.clim[1] >= max(0.0, values.max())
    fixed = layer_style(
        sample,
        "elevation",
        radius_m=world.radius_m,
        elevation_range=(-12_000.0, 8_000.0),
    )
    assert fixed.clim == (-12_000.0, 8_000.0)
    fixed_map = elevation_colormap(fixed.clim)
    np.testing.assert_allclose(
        fixed_map(0.6)[:3], np.array([244, 241, 220]) / 255, atol=0.01
    )


def test_elevation_colormap_has_bathymetry_and_hypsometric_steps():
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
    assert cmap.N >= 256


def test_one_sided_elevation_colormaps_crop_to_land_and_ocean_ranges():
    land = elevation_colormap((100.0, 1_000.0))
    full_land = elevation_colormap((0.0, 1_000.0))
    ocean = elevation_colormap((-1_000.0, -100.0))
    full_ocean = elevation_colormap((-1_000.0, 0.0))

    np.testing.assert_allclose(land(0.0), full_land(0.1), atol=1e-3)
    np.testing.assert_allclose(land(1.0), full_land(1.0), atol=1e-3)
    np.testing.assert_allclose(ocean(0.0), full_ocean(0.0), atol=1e-3)
    np.testing.assert_allclose(ocean(1.0), full_ocean(0.9), atol=1e-3)
    assert np.isfinite(land(np.linspace(0.0, 1.0, 257))).all()
    assert np.isfinite(ocean(np.linspace(0.0, 1.0, 257))).all()


def test_variation_and_tectonic_styles_are_signed_meter_channels():
    config = WorldgenConfig(seed=17, subdivision_frequency=2)
    config = replace(
        config,
        elevation=replace(
            config.elevation,
            variation=replace(config.elevation.variation, amplitude_percent=0.01),
        ),
    )
    world = generate_world(config)
    sample = _sample(world)
    for layer, fraction_name in (
        ("terrain-variation", "terrain_variation"),
        ("tectonic-relief", "tectonic_relief"),
        ("convergent-relief", "convergent_relief"),
        ("divergent-relief", "divergent_relief"),
        ("transform-relief", "transform_relief"),
        ("shear-relief", "shear_relief"),
        ("volcanic-relief", "volcanic_relief"),
    ):
        style = layer_style(sample, layer, radius_m=world.radius_m)
        np.testing.assert_array_equal(
            style.values, getattr(sample.elevation, fraction_name) * world.radius_m
        )
        assert style.cmap == "coolwarm"
        assert style.clim[0] < 0.0 < style.clim[1]


def test_categorical_styles_use_named_sampled_region_ids():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    sample = _sample(world)
    for layer in ("plates", "crust", "crust-regions"):
        style = layer_style(sample, layer, radius_m=world.radius_m)
        assert style.categorical
        assert len(style.values) == len(world.mesh.vertices)
    np.testing.assert_array_equal(
        layer_style(sample, "crust-regions", radius_m=world.radius_m).values,
        world.geology.crust_region_ids,
    )
    for layer in ("continental-weight", "max-plate-weight"):
        assert layer_style(sample, layer, radius_m=world.radius_m).clim == (0.0, 1.0)


def test_surface_layer_styles_use_surface_measurements_and_fixed_units():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    count = len(world.mesh.vertices)
    land_height = np.zeros(count)
    water_depth = np.zeros(count)
    slope_degrees = np.zeros(count)
    local_relief = np.zeros(count)
    roughness = np.zeros(count)
    water_depth[0] = 4_300.0
    land_height[1] = 320.0
    slope_degrees[2] = 65.0
    local_relief[2] = 2_500.0
    roughness[2] = 650.0
    surface = SurfaceResult(
        land_height=land_height,
        water_depth=water_depth,
        slope_degrees=slope_degrees,
        local_relief=local_relief,
        roughness=roughness,
    )
    expected = {
        "land-height": (land_height, "Land height (m)", "YlOrBr", (0.0, 320.0)),
        "water-depth": (
            water_depth,
            "Water depth below sea level (m)",
            "Blues",
            (0.0, 4_300.0),
        ),
        "slope": (slope_degrees, "Surface slope (degrees)", "magma", (0.0, 90.0)),
        "local-relief": (local_relief, "Local relief (m)", "viridis", (0.0, 2_500.0)),
        "roughness": (
            roughness,
            "Detrended roughness (m RMS)",
            "inferno",
            (0.0, 650.0),
        ),
    }
    for name, (values, title, cmap, clim) in expected.items():
        style = layer_style(
            _sample(world), name, radius_m=world.radius_m, surface=surface
        )
        assert style.title == title
        assert style.cmap == cmap
        assert style.clim == clim
        np.testing.assert_array_equal(style.values, values)
    assert layer_style(
        _sample(world), "slope", radius_m=world.radius_m, surface=surface
    ).clim == (0.0, 90.0)
