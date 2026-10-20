import numpy as np

from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def _identity_warp() -> ShearWarpField:
    return ShearWarpField(
        config=ShearWarpConfig(iterations=0),
        shear=lambda plane, iteration, axis, frequency: np.zeros(len(plane)),
    )


def _manual_regions(seeds: np.ndarray, warp: ShearWarpField | None = None):
    return WarpedVoronoiField(
        warp=warp or _identity_warp(), voronoi=VoronoiField3D(seeds)
    )


def test_motion_field_uses_owner_rotation_at_original_query_position() -> None:
    regions = _manual_regions(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
    motion = RegionRotationField(
        regions=regions,
        angular_velocity=np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
    )
    point = np.array([[0.75, 0.0, 0.5]])

    velocity = motion.sample(point)

    np.testing.assert_allclose(velocity, [[0.0, -0.5, 0.0]])
    assert not velocity.flags.writeable
    assert not motion.angular_velocity.flags.writeable


def test_motion_field_uses_warped_owner_but_unwarped_motion_position() -> None:
    def translation_shear(
        plane_positions: np.ndarray, iteration: int, axis: int, frequency: float
    ):
        return np.full(len(plane_positions), (0.0, 1.0, 0.25)[axis])

    warp = ShearWarpField(
        config=ShearWarpConfig(iterations=1, amplitude=1.0, gain=1.0),
        shear=translation_shear,
    )
    regions = _manual_regions(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), warp)
    motion = RegionRotationField(
        regions=regions,
        angular_velocity=np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
    )

    np.testing.assert_array_equal(
        motion.sample(np.array([[0.75, 0.0, 0.5]])), [[1.0, 0.0, -1.5]]
    )


def test_equal_region_rotations_form_one_rigid_velocity_field() -> None:
    regions = _manual_regions(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
    angular_velocity = np.array([[0.0, 0.0, 0.75], [0.0, 0.0, 0.75]])
    motion = RegionRotationField(regions, angular_velocity)
    positions = np.array([[0.8, 0.1, 0.4], [0.1, 0.8, 0.4]])

    velocities = motion.sample(positions)

    np.testing.assert_allclose(velocities, np.cross(angular_velocity[0], positions))


def test_selected_region_rotations_use_explicit_ids_at_original_positions() -> None:
    regions = _manual_regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    motion = RegionRotationField(
        regions,
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
    )
    positions = np.array([[0.25, 1.0, 0.0], [0.25, 1.0, 0.0]])

    velocities = motion.sample_regions(positions, np.array([0, 1]))

    np.testing.assert_allclose(velocities, [[-1.0, 0.25, 0.0], [-2.0, 0.5, 0.0]])
    assert not velocities.flags.writeable


def test_selected_region_rotations_preserve_repeated_ids_and_empty_shape() -> None:
    motion = RegionRotationField(
        _manual_regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])),
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


def test_selected_region_rotations_ignore_warped_query_coordinates() -> None:
    def affine_shear(
        plane_positions: np.ndarray, iteration: int, axis: int, frequency: float
    ):
        return plane_positions[:, 0] if axis == 0 else np.zeros(len(plane_positions))

    warp = ShearWarpField(
        config=ShearWarpConfig(iterations=1, amplitude=1.0, gain=1.0),
        shear=affine_shear,
    )
    regions = _manual_regions(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]), warp)
    motion = RegionRotationField(
        regions,
        np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 2.0]]),
    )
    positions = np.array([[0.25, 1.0, 0.0], [0.25, 1.0, 0.0]])

    velocities = motion.sample_regions(positions, np.array([0, 1]))

    np.testing.assert_allclose(velocities, [[-1.0, 0.25, 0.0], [-2.0, 0.5, 0.0]])
