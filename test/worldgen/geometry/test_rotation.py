import numpy as np
import pytest

from src.worldgen.geometry.rotation import rotation_vectors, rotational_velocity


def test_rotation_vectors_normalize_axes_and_preserve_signed_speed() -> None:
    axes = np.array([[2.0, 0.0, 0.0], [0.0, -3.0, 0.0], [1.0, 2.0, 2.0]])
    speeds = np.array([2.0, -4.0, 3.0])

    rotations = rotation_vectors(axes, speeds)

    np.testing.assert_allclose(
        rotations, [[2.0, 0.0, 0.0], [0.0, 4.0, 0.0], [1.0, 2.0, 2.0]]
    )


def test_rotational_velocity_uses_right_hand_rule_and_scales_with_position() -> None:
    rotation = np.array([0.0, 0.0, 2.0])
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.25, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )

    velocities = rotational_velocity(positions, rotation)

    np.testing.assert_allclose(
        velocities,
        [
            [0.0, 2.0, 0.0],
            [-2.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.0, 0.0],
        ],
    )
    np.testing.assert_allclose(np.sum(positions * velocities, axis=1), 0.0)
    np.testing.assert_allclose(rotational_velocity(positions, -rotation), -velocities)


def test_rotational_velocity_accepts_paired_angular_velocities() -> None:
    positions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    rotations = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, -3.0]])

    np.testing.assert_allclose(
        rotational_velocity(positions, rotations), [[0.0, 2.0, 0.0], [3.0, 0.0, 0.0]]
    )


def test_rotation_vectors_reject_zero_axis_even_for_zero_speed() -> None:
    with pytest.raises(ValueError, match=r"^Rotation axes must be nonzero\.$"):
        rotation_vectors(np.array([[0.0, 0.0, 0.0]]), np.array([0.0]))


def test_rotation_vectors_allow_near_origin_axis_and_zero_speed() -> None:
    rotations = rotation_vectors(
        np.array([[1e-9, 0.0, 0.0], [0.0, 2.0, 0.0]]),
        np.array([2.0, 0.0]),
    )

    np.testing.assert_allclose(rotations, [[2.0, 0.0, 0.0], [0.0, 0.0, 0.0]])


def test_rotation_primitives_handle_empty_batches() -> None:
    assert rotation_vectors(np.empty((0, 3)), np.empty(0)).shape == (0, 3)
    assert rotational_velocity(np.empty((0, 3)), np.array([0.0, 0.0, 1.0])).shape == (
        0,
        3,
    )
