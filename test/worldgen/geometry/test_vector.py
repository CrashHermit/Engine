import numpy as np

from src.worldgen.geometry.vector import relative_motion_components


def test_relative_motion_splits_normal_opening_and_tangent_sliding():
    first = np.array([[0.0, 0, 0]])
    second = np.array([[-2.0, 3, 4]])
    normal = np.array([[1.0, 0, 0]])
    opening, sliding = relative_motion_components(first, second, normal)
    np.testing.assert_array_equal(opening, [-2])
    assert 4.99 < sliding[0] < 5.0
    reverse_opening, reverse_sliding = relative_motion_components(
        second, first, -normal
    )
    np.testing.assert_array_equal(reverse_opening, opening)
    np.testing.assert_array_equal(reverse_sliding, sliding)
    zero = relative_motion_components(first, first, normal)
    np.testing.assert_array_equal(zero[0], [0])
    np.testing.assert_array_equal(zero[1], [0])
    empty = relative_motion_components(
        np.empty((0, 3)), np.empty((0, 3)), np.empty((0, 3))
    )
    assert empty[0].shape == empty[1].shape == (0,)


def test_regularized_sliding_is_zero_preserving_and_c1_at_origin():
    first = np.zeros((5, 3))
    second = np.array(
        [[0.0, 0, 0], [0.001, 0, 0], [-0.001, 0, 0], [0, 0.01, 0], [0, -0.01, 0]]
    )
    normals = np.tile([1.0, 0, 0], (len(first), 1))
    opening, sliding = relative_motion_components(first, second, normals)
    assert opening[0] == 0.0
    assert sliding[0] == 0.0
    np.testing.assert_allclose(sliding[1:3], 0.0)
    np.testing.assert_allclose(sliding[3:], sliding[3])
    assert np.all(sliding >= 0.0)

    reversed_opening, reversed_sliding = relative_motion_components(
        second, first, -normals
    )
    np.testing.assert_allclose(reversed_opening, opening)
    np.testing.assert_allclose(reversed_sliding, sliding)


def test_regularized_tangent_magnitude_has_zero_derivative_at_origin():
    normals = np.tile([1.0, 0, 0], (2, 1))
    delta = 1e-7
    _, sliding = relative_motion_components(
        np.zeros((2, 3)),
        np.array([[0.0, delta, 0], [0.0, -delta, 0]]),
        normals,
    )
    np.testing.assert_allclose(sliding / delta, 0.0, atol=1e-5)
