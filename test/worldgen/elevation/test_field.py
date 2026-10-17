from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world


def _world():
    return generate_world(WorldgenConfig(seed=2026, subdivision_frequency=5))


def test_arbitrary_samples_are_independent_of_batch_order_and_resolution():
    world = _world()
    field = world.elevation_field
    points = np.random.default_rng(13).normal(size=(21, 3))
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    full = field.sample(points)
    order = np.array([12, 4, 0, 20, 7])
    subset = field.sample(points[order])
    for name in (
        "base_elevation",
        "tectonic_relief",
        "volcanic_relief",
        "elevation",
        "margin_distance",
    ):
        np.testing.assert_array_equal(getattr(subset, name), getattr(full, name)[order])
        single = field.sample(points[order[:1]])
        np.testing.assert_array_equal(
            getattr(single, name), getattr(full, name)[order[:1]]
        )
    np.testing.assert_array_equal(full.land_mask, full.elevation >= 0.0)
    assert not full.elevation.flags.writeable


def test_crust_boundary_samples_are_shelf_breaks_not_nearest_cell_values():
    world = _world()
    boundary = world.elevation_field.crust_boundary
    points = boundary.starts + boundary.ends
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    values = world.elevation_field.sample(points)
    np.testing.assert_allclose(values.margin_distance, 0.0, atol=1e-10)
    expected = (
        -world.elevation_field.config.shelf_depth_percent * world.radius_m / 100.0
    )
    np.testing.assert_allclose(values.base_elevation, expected, atol=1e-7)


def test_full_elevation_has_no_height_jump_across_plate_boundaries():
    world = _world()
    boundary = world.elevation_field.plate_boundary
    ids = np.arange(0, len(boundary.starts), max(1, len(boundary.starts) // 30))
    midpoints = boundary.starts[ids] + boundary.ends[ids]
    midpoints /= np.linalg.norm(midpoints, axis=1, keepdims=True)
    across = np.cross(boundary.starts[ids], boundary.ends[ids])
    across /= np.linalg.norm(across, axis=1, keepdims=True)
    left = midpoints + across * 1e-8
    right = midpoints - across * 1e-8
    left /= np.linalg.norm(left, axis=1, keepdims=True)
    right /= np.linalg.norm(right, axis=1, keepdims=True)
    difference = np.abs(
        world.elevation_field.sample(left).elevation
        - world.elevation_field.sample(right).elevation
    )
    assert np.all(difference < 1.0)


def test_radius_scaling_and_empty_queries_work_without_rebuilding_geography():
    world = _world()
    field = world.elevation_field
    points = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0]])
    original = field.sample(points)
    doubled = replace(field, radius_m=field.radius_m * 2.0).sample(points)
    np.testing.assert_array_equal(doubled.elevation, original.elevation * 2.0)
    np.testing.assert_array_equal(doubled.margin_distance, original.margin_distance)
    np.testing.assert_array_equal(
        doubled.elevation_range_m, np.asarray(original.elevation_range_m) * 2.0
    )
    assert original.elevation.min() >= original.elevation_range_m[0]
    assert original.elevation.max() <= original.elevation_range_m[1]
    empty = field.sample(np.empty((0, 3)))
    assert empty.elevation.shape == (0,)
    assert empty.land_mask.shape == (0,)
