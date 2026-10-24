from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.field.differential import ScalarSample
from src.worldgen.surface.config import SurfaceConfig
from src.worldgen.surface.field import SurfaceField, _neighborhood_metrics


def _constant_height(height_m: float):
    return lambda positions: np.full(len(positions), height_m, dtype=np.float64)


def _constant_height_with_gradient(height_m: float):
    return lambda positions: ScalarSample(
        np.full(len(positions), height_m, dtype=np.float64),
        np.zeros((len(positions), 3), dtype=np.float64),
    )


def test_constant_elevation_separates_land_and_water_without_neighborhood_relief():
    positions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    for value, land, water in (
        (-100.0, 0.0, 100.0),
        (0.0, 0.0, 0.0),
        (100.0, 100.0, 0.0),
    ):
        field = SurfaceField(
            SurfaceConfig(),
            _constant_height(value),
            6_371_000.0,
            _constant_height_with_gradient(value),
        )
        result = field.sample(positions)
        np.testing.assert_array_equal(result.land_height, land)
        np.testing.assert_array_equal(result.water_depth, water)
        np.testing.assert_array_equal(result.slope_degrees, 0.0)
        np.testing.assert_array_equal(result.local_relief, 0.0)
        np.testing.assert_array_equal(result.roughness, 0.0)
        for name in result.__dataclass_fields__:
            values = getattr(result, name)
            assert values.dtype == np.float64
            assert values.shape == (len(positions),)
            assert not values.flags.writeable


def test_plane_fit_detrends_roughness_without_dependence_on_absolute_altitude():
    bearing = 2.0 * np.pi * np.arange(8, dtype=np.float64) / 8.0
    cosine = np.cos(bearing)
    sine = np.sin(bearing)
    distance_m = 2_500.0
    outputs = []
    for vertical_offset in (0.0, 100_000.0):
        center = np.array([100.0 + vertical_offset])
        ring = (100.0 + vertical_offset + distance_m * (0.3 * cosine + 0.4 * sine))[
            None, :
        ]
        relief, roughness = _neighborhood_metrics(center, ring, distance_m)
        np.testing.assert_allclose(relief, np.ptp(np.concatenate((center, ring[0]))))
        np.testing.assert_allclose(roughness, 0.0, atol=1e-9)
        outputs.append((relief, roughness))
    for original, offset in zip(outputs[0], outputs[1], strict=True):
        np.testing.assert_allclose(original, offset, rtol=0.0, atol=1e-9)


def test_center_peak_and_pit_contribute_to_sampled_relief_and_roughness():
    ring = np.zeros((1, 8), dtype=np.float64)
    pit = _neighborhood_metrics(np.array([-300.0]), ring, 1_000.0)
    peak = _neighborhood_metrics(np.array([300.0]), ring, 1_000.0)
    expected_roughness = 300.0 * np.sqrt(8.0) / 9.0
    for relief, roughness in (pit, peak):
        np.testing.assert_allclose(relief, 300.0, atol=1e-12)
        np.testing.assert_allclose(roughness, expected_roughness, atol=1e-12)


def test_point_slope_and_normals_are_analytic_while_relief_uses_footprint():
    radius_m = 6_371_000.0
    base_height = 500.0
    height_scale = 12_000.0
    positions = np.array([[1.0, 0.0, 0.0]])
    evaluator = lambda points: base_height + height_scale * points[:, 2]
    differential = lambda points: ScalarSample(
        evaluator(points), np.broadcast_to([0.0, 0.0, height_scale], points.shape)
    )
    measured = []
    for footprint_circumference_percent in (0.05, 1.0):
        field = SurfaceField(
            SurfaceConfig(
                footprint_circumference_percent=footprint_circumference_percent
            ),
            evaluator,
            radius_m,
            differential,
        )
        result = field.sample(positions)
        angular_radius = footprint_circumference_percent * 2.0 * np.pi / 100.0
        expected_slope = np.degrees(
            np.arctan2(abs(height_scale), radius_m + base_height)
        )
        expected_relief = 2.0 * abs(height_scale * np.sin(angular_radius))
        np.testing.assert_allclose(result.slope_degrees, expected_slope, atol=1e-10)
        np.testing.assert_allclose(result.local_relief, expected_relief, atol=1e-10)
        np.testing.assert_allclose(result.roughness, 0.0, atol=1e-9)
        expected_normal = np.array([[radius_m + base_height, 0.0, -height_scale]])
        expected_normal /= np.linalg.norm(expected_normal, axis=1, keepdims=True)
        np.testing.assert_allclose(field.sample_normals(positions), expected_normal)
        measured.append((result.slope_degrees.copy(), result.local_relief.copy()))
    np.testing.assert_array_equal(measured[0][0], measured[1][0])
    assert measured[0][1][0] != measured[1][1][0]


def test_empty_surface_queries_return_read_only_empty_arrays():
    field = SurfaceField(
        SurfaceConfig(),
        _constant_height(0.0),
        6_371_000.0,
        _constant_height_with_gradient(0.0),
    )
    result = field.sample(np.empty((0, 3)))
    for name in result.__dataclass_fields__:
        values = getattr(result, name)
        assert values.shape == (0,)
        assert not values.flags.writeable


def test_generated_surface_matches_meter_sampler_across_query_batches():
    world = generate_world(WorldgenConfig(seed=2026, subdivision_frequency=5))
    positions = world.mesh.vertices
    sampled = world.surface_field.sample(positions)
    permutation = np.random.default_rng(2026).permutation(len(positions))
    reordered = world.surface_field.sample(positions[permutation])
    first = world.surface_field.sample(positions[:1024])
    last = world.surface_field.sample(positions[1024:])
    for name in sampled.__dataclass_fields__:
        values = getattr(sampled, name)
        assert values.shape == (len(positions),)
        assert np.isfinite(values).all()
        assert not values.flags.writeable
        np.testing.assert_array_equal(getattr(reordered, name), values[permutation])
        np.testing.assert_array_equal(
            np.concatenate((getattr(first, name), getattr(last, name))), values
        )
    np.testing.assert_array_equal(
        world.surface_field.sample_elevation_meters(positions),
        world.field.sample_elevation_meters(positions, radius_m=world.radius_m),
    )
    for name in world.surface.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(sampled, name), getattr(world.surface, name)
        )


def test_surface_metrics_scale_with_radius_but_slope_does_not():
    world = generate_world(WorldgenConfig(seed=2026, subdivision_frequency=5))
    positions = world.mesh.vertices[:12]
    original = SurfaceField(
        world.surface_field.config,
        lambda points: world.field.sample_elevation_meters(
            points, radius_m=6_371_000.0
        ),
        6_371_000.0,
        lambda points: world.field.sample_elevation_meters_with_gradient(
            points, radius_m=6_371_000.0
        ),
    ).sample(positions)
    larger = SurfaceField(
        world.surface_field.config,
        lambda points: world.field.sample_elevation_meters(
            points, radius_m=12_742_000.0
        ),
        12_742_000.0,
        lambda points: world.field.sample_elevation_meters_with_gradient(
            points, radius_m=12_742_000.0
        ),
    ).sample(positions)
    for name in ("land_height", "water_depth", "local_relief", "roughness"):
        np.testing.assert_allclose(
            getattr(larger, name), 2.0 * getattr(original, name), rtol=1e-12, atol=1e-8
        )
    np.testing.assert_allclose(
        larger.slope_degrees, original.slope_degrees, rtol=1e-12, atol=1e-10
    )


def test_surface_footprint_does_not_change_world_field_samples():
    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    narrow = generate_world(config)
    broad = generate_world(
        replace(
            config,
            surface=replace(config.surface, footprint_circumference_percent=0.1),
        )
    )
    for name in narrow.geology.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(narrow.geology, name), getattr(broad.geology, name)
        )
    for name in narrow.elevation.__dataclass_fields__:
        np.testing.assert_array_equal(
            getattr(narrow.elevation, name), getattr(broad.elevation, name)
        )
    np.testing.assert_array_equal(
        narrow.surface_field.sample_elevation_meters(narrow.mesh.vertices),
        broad.surface_field.sample_elevation_meters(broad.mesh.vertices),
    )


def test_radial_elevation_gradient_does_not_create_surface_slope():
    amplitude = 10_000.0
    points = np.array([[1.0, 0.0, 0.0], [0.6, 0.8, 0.0], [0.0, 0.0, -1.0]])
    height = lambda q: amplitude * np.einsum("ni,ni->n", q, q)
    differential = lambda q: ScalarSample(height(q), 2 * amplitude * q)
    field = SurfaceField(SurfaceConfig(), height, 6_371_000.0, differential)
    np.testing.assert_allclose(field.sample(points).slope_degrees, 0.0, atol=1e-12)
    np.testing.assert_allclose(field.sample_normals(points), points, atol=1e-12)
