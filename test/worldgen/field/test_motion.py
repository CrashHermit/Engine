import numpy as np

from src.worldgen.field.motion import RegionRotationField, RotationField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def test_motion_field_uses_source_owner_at_source_query_position() -> None:
    partition = VoronoiField3D(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
    motion = RegionRotationField(
        partition=partition,
        angular_velocity=np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
    )
    point = np.array([[0.75, 0.0, 0.5]])

    velocity = motion.sample(point)

    np.testing.assert_allclose(velocity, [[0.0, -0.5, 0.0]])
    assert not velocity.flags.writeable
    assert not motion.angular_velocity.flags.writeable


def test_outer_warp_changes_ownership_and_motion_at_the_same_source_position() -> None:
    def translation_shear(
        plane_positions: np.ndarray, iteration: int, axis: int, frequency: float
    ):
        return np.full(len(plane_positions), (0.0, 1.0, 0.25)[axis])

    warp = ShearWarpField(
        config=ShearWarpConfig(iterations=1, amplitude=1.0, gain=1.0),
        shear=translation_shear,
    )
    partition = VoronoiField3D(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
    motion = RegionRotationField(
        partition=partition,
        angular_velocity=np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
    )

    point = np.array([[0.75, 0.0, 0.5]])
    source = warp.sample(point)
    np.testing.assert_array_equal(motion.sample(point), [[0.0, -0.5, 0.0]])
    np.testing.assert_array_equal(source, [[0.75, 1.0, 0.75]])
    np.testing.assert_array_equal(motion.sample(source), [[1.5, 0.0, -1.5]])


def test_equal_region_rotations_form_one_rigid_velocity_field() -> None:
    partition = VoronoiField3D(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
    angular_velocity = np.array([[0.0, 0.0, 0.75], [0.0, 0.0, 0.75]])
    motion = RegionRotationField(partition, angular_velocity)
    positions = np.array([[0.8, 0.1, 0.4], [0.1, 0.8, 0.4]])

    velocities = motion.sample(positions)

    np.testing.assert_allclose(velocities, np.cross(angular_velocity[0], positions))


def test_selected_region_rotations_use_explicit_ids_at_source_positions() -> None:
    partition = VoronoiField3D(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    motion = RegionRotationField(
        partition,
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
    )
    positions = np.array([[0.25, 1.0, 0.0], [0.25, 1.0, 0.0]])

    velocities = motion.sample_regions(positions, np.array([0, 1]))

    np.testing.assert_allclose(velocities, [[-1.0, 0.25, 0.0], [-2.0, 0.5, 0.0]])
    assert not velocities.flags.writeable


def test_selected_region_rotations_preserve_repeated_ids_and_empty_shape() -> None:
    motion = RegionRotationField(
        VoronoiField3D(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])),
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
    )
    positions = np.array([[0.25, 1.0, 0.0], [0.5, 0.0, 1.0], [0.25, 1.0, 0.0]])

    velocities = motion.sample_regions(positions, np.array([1, 0, 1]))
    empty = motion.sample_regions(np.empty((0, 3)), np.empty(0, dtype=np.int64))

    np.testing.assert_allclose(
        velocities,
        [[-2.0, 0.5, 0.0], [0.0, 0.5, 0.0], [-2.0, 0.5, 0.0]],
    )
    assert not velocities.flags.writeable
    assert empty.shape == (0, 3)
    assert not empty.flags.writeable


def test_global_rotation_field_values_jacobian_and_empty_strided_batches():
    source_angular_velocity = np.array([0.0, 0.0, 2.0])
    rotation = RotationField(source_angular_velocity)
    source_angular_velocity[:] = 99.0
    points = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0],
            [3.0, 2.0, -1.0],
            [2.0, -1.0, 0.5],
            [0.2, 0.4, 0.6],
        ]
    )[::2]

    sample = rotation.sample_with_jacobian(points)
    empty = rotation.sample_with_jacobian(np.empty((0, 3)))
    expected_jacobian = np.array([[0.0, -2.0, 0.0], [2.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

    np.testing.assert_array_equal(sample.values, np.cross([0.0, 0.0, 2.0], points))
    np.testing.assert_array_equal(
        sample.jacobians, np.broadcast_to(expected_jacobian, (4, 3, 3))
    )
    np.testing.assert_array_equal(sample.values[1:3], [[0.0, 0.0, 0.0]] * 2)
    assert rotation.angular_velocity.tolist() == [0.0, 0.0, 2.0]
    assert not rotation.angular_velocity.flags.writeable
    assert not sample.values.flags.writeable
    assert not sample.jacobians.flags.writeable
    assert empty.values.shape == (0, 3)
    assert empty.jacobians.shape == (0, 3, 3)
    assert not empty.values.flags.writeable
    assert not empty.jacobians.flags.writeable


def test_regional_rotation_jacobians_use_shared_cartesian_derivative():
    motion = RegionRotationField(
        VoronoiField3D(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])),
        np.array([[1.0, 2.0, 3.0], [-2.0, 1.0, 0.5]]),
    )
    points = np.array([[0.3, -0.2, 0.7], [-0.1, 0.8, 0.4]])

    sample = motion.sample_regions_with_jacobian(points, np.array([0, 1]))
    step = 1e-6
    numerical = np.stack(
        [
            (
                motion.sample_regions(points + np.eye(3)[axis] * step, [0, 1])
                - motion.sample_regions(points - np.eye(3)[axis] * step, [0, 1])
            )
            / (2.0 * step)
            for axis in range(3)
        ],
        axis=-1,
    )

    np.testing.assert_allclose(sample.jacobians, numerical, rtol=1e-9, atol=1e-9)
    assert not sample.jacobians.flags.writeable
