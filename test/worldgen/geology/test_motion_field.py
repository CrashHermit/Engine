import copy

import numpy as np

from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.regions import build_warped_voronoi_field
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geology.motion import (
    PlateMotionConfig,
    build_plate_motion_field,
    generate_plate_motion,
)


def _assert_global_rng_unchanged(before: tuple, after: tuple) -> None:
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_generated_rotation_magnitudes_follow_configured_interval_and_rng() -> None:
    seeds = np.array([[3.0, 0.0, 0.0], [0.0, -2.0, 0.0], [1.0, 2.0, 3.0]])
    global_state = np.random.get_state()
    lower = generate_plate_motion(
        seeds,
        PlateMotionConfig(min_angular_speed=0.0, max_angular_speed=0.5),
        rng=np.random.default_rng(817),
    )
    repeated = generate_plate_motion(
        seeds,
        PlateMotionConfig(min_angular_speed=0.0, max_angular_speed=0.5),
        rng=np.random.default_rng(817),
    )
    full = generate_plate_motion(
        seeds,
        PlateMotionConfig(min_angular_speed=0.0, max_angular_speed=1.0),
        rng=np.random.default_rng(817),
    )

    np.testing.assert_array_equal(lower, repeated)
    np.testing.assert_allclose(lower, full * 0.5)
    magnitudes = np.linalg.norm(lower, axis=1)
    assert np.all(magnitudes >= 0.0)
    assert np.all(magnitudes <= 0.5)
    moved_seeds = generate_plate_motion(
        seeds + 4.0, PlateMotionConfig(0.0, 0.5), rng=np.random.default_rng(817)
    )
    np.testing.assert_array_equal(lower, moved_seeds)
    assert not lower.flags.writeable
    _assert_global_rng_unchanged(global_state, np.random.get_state())


def test_generated_motion_allows_zero_and_above_one_magnitudes() -> None:
    seeds = np.array([[2.0, 0.0, 0.0], [0.0, -3.0, 0.0]])
    stationary = generate_plate_motion(
        seeds,
        PlateMotionConfig(min_angular_speed=0.0, max_angular_speed=0.0),
        rng=np.random.default_rng(7),
    )
    unit = generate_plate_motion(
        seeds,
        PlateMotionConfig(min_angular_speed=1.0, max_angular_speed=1.0),
        rng=np.random.default_rng(7),
    )
    above_default = generate_plate_motion(
        seeds,
        PlateMotionConfig(min_angular_speed=2.0, max_angular_speed=2.0),
        rng=np.random.default_rng(7),
    )

    np.testing.assert_array_equal(stationary, np.zeros((2, 3)))
    np.testing.assert_allclose(np.linalg.norm(unit, axis=1), 1.0)
    np.testing.assert_allclose(np.linalg.norm(above_default, axis=1), 2.0)


def test_motion_is_not_clipped_and_scales_linearly_with_query_distance() -> None:
    partition = VoronoiField3D(np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]]))
    motion = build_plate_motion_field(
        partition,
        PlateMotionConfig(min_angular_speed=1.0, max_angular_speed=1.0),
        rng=np.random.default_rng(5),
    )
    axis = motion.angular_velocity[0]
    perpendicular = np.cross(axis, [1.0, 0.0, 0.0])
    perpendicular *= 3.0 / np.linalg.norm(perpendicular)
    positions = np.array([perpendicular, perpendicular * 0.5])

    velocities = motion.sample_regions(positions, np.array([0, 0]))

    assert np.linalg.norm(velocities[0]) > 1.0
    np.testing.assert_allclose(velocities[1], velocities[0] * 0.5)


def test_continuous_motion_is_batch_and_resolution_independent() -> None:
    regions = build_warped_voronoi_field(
        12,
        rng=np.random.default_rng(2026),
        noise_config=NoiseConfig(octaves=2, base_frequency=1.1),
        warp_config=ShearWarpConfig(iterations=2, amplitude=0.12),
        noise_seed=2026,
    )
    motion_rng = np.random.default_rng(2027)
    motion = build_plate_motion_field(
        regions.voronoi, PlateMotionConfig(), rng=motion_rng
    )
    motion_rng_state = copy.deepcopy(motion_rng.bit_generator.state)
    global_state = np.random.get_state()
    cube_points = np.random.default_rng(91).uniform(-1.0, 1.0, size=(41, 3))
    sphere_points, _ = generate_icosphere(3)
    positions = np.concatenate((cube_points, sphere_points))

    expected = motion.sample(positions)
    order = np.random.default_rng(19).permutation(len(positions))
    np.testing.assert_array_equal(motion.sample(positions[order]), expected[order])
    np.testing.assert_array_equal(motion.sample(positions[7:8]), expected[7:8])
    split_batches = np.concatenate(
        (motion.sample(positions[:13]), motion.sample(positions[13:]))
    )
    np.testing.assert_array_equal(split_batches, expected)
    assert motion.sample(np.empty((0, 3))).shape == (0, 3)
    origin_velocity = motion.sample(np.array([[0.0, 0.0, 0.0]]))
    np.testing.assert_array_equal(origin_velocity, [[0.0, 0.0, 0.0]])
    assert motion_rng.bit_generator.state == motion_rng_state
    _assert_global_rng_unchanged(global_state, np.random.get_state())
