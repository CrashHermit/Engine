from dataclasses import replace
from types import SimpleNamespace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation.config import ImpactConfig
from src.worldgen.generate import generate_world
from src.worldgen.geometry.spherical import spherical_ring
from src.worldgen.surface import SurfaceConfig, SurfaceField
from src.worldgen.surface.field import _neighborhood_metrics


class _AnalyticElevationField:
    def __init__(self, radius_m: float, evaluator) -> None:
        self.radius_m = radius_m
        self.evaluator = evaluator

    def sample(self, positions: np.ndarray) -> SimpleNamespace:
        return SimpleNamespace(
            elevation=np.asarray(self.evaluator(positions), dtype=np.float64)
        )


def test_constant_elevation_separates_land_and_water_without_neighborhood_relief() -> (
    None
):
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    for value, land, water in (
        (-100.0, 0.0, 100.0),
        (0.0, 0.0, 0.0),
        (100.0, 100.0, 0.0),
    ):
        field = SurfaceField(
            SurfaceConfig(),
            _AnalyticElevationField(
                6_371_000.0, lambda points: np.full(len(points), value)
            ),
        )
        result = field.sample(positions)

        np.testing.assert_array_equal(result.land_height, land)
        np.testing.assert_array_equal(result.water_depth, water)
        np.testing.assert_array_equal(result.slope_degrees, 0.0)
        np.testing.assert_array_equal(result.local_relief, 0.0)
        np.testing.assert_array_equal(result.roughness, 0.0)
        for array in (
            result.land_height,
            result.water_depth,
            result.slope_degrees,
            result.local_relief,
            result.roughness,
        ):
            assert array.dtype == np.float64
            assert array.shape == (len(positions),)
            assert not array.flags.writeable


def test_plane_fit_recovers_slope_and_detrends_roughness() -> None:
    bearing = 2.0 * np.pi * np.arange(8, dtype=np.float64) / 8.0
    cosine = np.cos(bearing)
    sine = np.sin(bearing)
    distance_m = 2_500.0
    expected_slope = np.degrees(np.arctan(0.5))
    outputs = []

    for vertical_offset in (0.0, 100_000.0):
        center = np.array([100.0 + vertical_offset])
        ring = (100.0 + vertical_offset + distance_m * (0.3 * cosine + 0.4 * sine))[
            None, :
        ]
        slope, relief, roughness = _neighborhood_metrics(center, ring, distance_m)
        expected_relief = np.ptp(np.concatenate((center, ring[0])))

        np.testing.assert_allclose(slope, expected_slope, atol=1e-9)
        np.testing.assert_allclose(relief, expected_relief, atol=1e-9)
        np.testing.assert_allclose(roughness, 0.0, atol=1e-9)
        outputs.append((slope, relief, roughness))

    for original, offset in zip(outputs[0], outputs[1], strict=True):
        np.testing.assert_allclose(original, offset, rtol=0.0, atol=1e-9)


def test_center_peak_and_pit_contribute_to_sampled_relief_and_roughness() -> None:
    ring = np.zeros((1, 8), dtype=np.float64)
    pit = _neighborhood_metrics(np.array([-300.0]), ring, 1_000.0)
    peak = _neighborhood_metrics(np.array([300.0]), ring, 1_000.0)
    expected_roughness = 300.0 * np.sqrt(8.0) / 9.0

    for slope, relief, roughness in (pit, peak):
        np.testing.assert_allclose(slope, 0.0, atol=1e-12)
        np.testing.assert_allclose(relief, 300.0, atol=1e-12)
        np.testing.assert_allclose(roughness, expected_roughness, atol=1e-12)


def test_spherical_linear_height_field_uses_configured_circumference_footprint() -> (
    None
):
    radius_m = 6_371_000.0
    base_height = 500.0
    height_scale = 12_000.0
    positions = np.array([[1.0, 0.0, 0.0]])
    evaluator = lambda points: base_height + height_scale * points[:, 2]
    measured = []

    for radius_percent in (0.05, 1.0):
        field = SurfaceField(
            SurfaceConfig(radius_percent=radius_percent),
            _AnalyticElevationField(radius_m, evaluator),
        )
        result = field.sample(positions)
        angular_radius = radius_percent * 2.0 * np.pi / 100.0
        distance_m = radius_m * angular_radius
        expected_slope = np.degrees(
            np.arctan(abs(height_scale) * np.sin(angular_radius) / distance_m)
        )
        expected_relief = 2.0 * abs(height_scale * np.sin(angular_radius))

        np.testing.assert_allclose(result.slope_degrees, expected_slope, atol=1e-10)
        np.testing.assert_allclose(result.local_relief, expected_relief, atol=1e-10)
        np.testing.assert_allclose(result.roughness, 0.0, atol=1e-9)
        measured.append((result.slope_degrees.copy(), result.local_relief.copy()))

    assert measured[0][0][0] != measured[1][0][0]
    assert measured[0][1][0] != measured[1][1][0]


def test_empty_surface_queries_return_read_only_empty_arrays() -> None:
    field = SurfaceField(
        SurfaceConfig(),
        _AnalyticElevationField(6_371_000.0, lambda points: np.zeros(len(points))),
    )

    result = field.sample(np.empty((0, 3)))

    for array in (
        result.land_height,
        result.water_depth,
        result.slope_degrees,
        result.local_relief,
        result.roughness,
    ):
        assert array.shape == (0,)
        assert not array.flags.writeable


def test_generated_surface_matches_retained_field_across_query_batches() -> None:
    world = generate_world(WorldgenConfig(seed=2026, subdivision_frequency=5))
    mesh_positions = world.mesh.vertices
    impacts = world.elevation_field.impacts
    flank_angle = 0.75 * impacts.radii_percent[0] * 2.0 * np.pi / 100.0
    impact_flank = spherical_ring(impacts.centers[:1], flank_angle)[0, 0]
    positions = np.concatenate(
        (
            mesh_positions[np.arange(1017) % len(mesh_positions)],
            impacts.centers[:3],
            impact_flank[None, :],
            np.array(
                [
                    [1.0, 0.0, 0.0],
                    [-1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [-np.sqrt(0.5), np.sqrt(0.5), 0.0],
                ]
            ),
        )
    )
    sampled = world.surface_field.sample(positions)
    permutation = np.random.default_rng(2026).permutation(len(positions))
    reordered = world.surface_field.sample(positions[permutation])
    first = world.surface_field.sample(positions[:1024])
    last = world.surface_field.sample(positions[1024:])

    for name in (
        "land_height",
        "water_depth",
        "slope_degrees",
        "local_relief",
        "roughness",
    ):
        values = getattr(sampled, name)
        assert values.shape == (len(positions),)
        assert np.isfinite(values).all()
        assert not values.flags.writeable
        np.testing.assert_array_equal(getattr(reordered, name), values[permutation])
        np.testing.assert_array_equal(
            np.concatenate((getattr(first, name), getattr(last, name))), values
        )

    center_elevation = world.elevation_field.sample(positions).elevation
    supplied_center = world.surface_field.sample(
        positions, center_elevation=center_elevation
    )
    mesh_surface = world.surface_field.sample(
        mesh_positions, center_elevation=world.elevation.elevation
    )
    for name in (
        "land_height",
        "water_depth",
        "slope_degrees",
        "local_relief",
        "roughness",
    ):
        np.testing.assert_array_equal(
            getattr(supplied_center, name), getattr(sampled, name)
        )
        np.testing.assert_array_equal(
            getattr(mesh_surface, name), getattr(world.surface, name)
        )

    np.testing.assert_array_equal(
        world.elevation.elevation,
        world.surface.land_height - world.surface.water_depth,
    )


def test_surface_measurements_scale_with_retained_planet_radius() -> None:
    world = generate_world(WorldgenConfig(seed=2026, subdivision_frequency=5))
    positions = world.mesh.vertices[:12]
    original = world.surface_field.sample(positions)
    larger_elevation = replace(
        world.elevation_field, radius_m=world.elevation_field.radius_m * 2.0
    )
    larger = SurfaceField(world.surface_field.config, larger_elevation).sample(
        positions
    )

    for name in ("land_height", "water_depth", "local_relief", "roughness"):
        np.testing.assert_allclose(
            getattr(larger, name),
            2.0 * getattr(original, name),
            rtol=1e-12,
            atol=1e-8,
        )
    np.testing.assert_allclose(
        larger.slope_degrees, original.slope_degrees, rtol=1e-12, atol=1e-10
    )


def test_surface_footprint_does_not_change_geology_or_elevation_sources() -> None:
    elevation = replace(
        WorldgenConfig().elevation,
        impacts=ImpactConfig(
            count=1,
            min_radius_percent=1.0,
            max_radius_percent=1.0,
            min_depth_percent=0.02,
            max_depth_percent=0.02,
            min_sharpness=2.0,
            max_sharpness=2.0,
        ),
    )
    config = WorldgenConfig(seed=2026, subdivision_frequency=5, elevation=elevation)
    narrow = generate_world(config)
    broad_config = replace(config, surface=replace(config.surface, radius_percent=0.1))
    broad = generate_world(broad_config)

    for name in (
        "coastal_elevation",
        "tectonic_relief",
        "volcanic_relief",
        "impact_relief",
        "terrain_variation",
        "elevation",
        "margin_distance",
        "crust_boundary_edge_indices",
    ):
        np.testing.assert_array_equal(
            getattr(narrow.elevation, name), getattr(broad.elevation, name)
        )
    for name in (
        "plate_ids",
        "plate_rotation",
        "plate_velocity",
        "boundary_convergence",
        "boundary_divergence",
        "boundary_shear",
    ):
        np.testing.assert_array_equal(
            getattr(narrow.geology, name), getattr(broad.geology, name)
        )
    np.testing.assert_array_equal(
        narrow.geology.crust.region_ids, broad.geology.crust.region_ids
    )
    np.testing.assert_array_equal(
        narrow.geology.crust.region_effective_density,
        broad.geology.crust.region_effective_density,
    )

    impact = narrow.elevation_field.impacts
    center = impact.centers[0]
    flank_angle = 0.75 * impact.radii_percent[0] * 2.0 * np.pi / 100.0
    flank = spherical_ring(center[None, :], flank_angle)[0, 0]
    narrow_flank = narrow.surface_field.sample(flank[None, :])
    broad_flank = broad.surface_field.sample(flank[None, :])
    assert narrow_flank.slope_degrees[0] != broad_flank.slope_degrees[0]
    assert narrow_flank.local_relief[0] != broad_flank.local_relief[0]
