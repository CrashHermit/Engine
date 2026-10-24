import numpy as np

from src.worldgen.field.axis import AxialCoordinateField


def test_axial_coordinate_is_linear_off_sphere_with_constant_gradient() -> None:
    field = AxialCoordinateField(np.array([0.0, 0.0, 4.0]))
    positions = np.array(
        [
            [0.0, 0.0, 2.5],
            [0.0, 0.0, -3.0],
            [2.0, -1.0, 0.0],
            [1.0, 2.0, 3.0],
            [0.0, 0.0, 0.0],
        ]
    )

    sample = field.sample_with_gradient(positions)

    np.testing.assert_array_equal(sample.values, [2.5, -3.0, 0.0, 3.0, 0.0])
    np.testing.assert_array_equal(
        sample.gradients, np.broadcast_to([0.0, 0.0, 1.0], (5, 3))
    )
    np.testing.assert_array_equal(field.sample(positions), sample.values)
    assert not field.direction.flags.writeable
    assert not sample.values.flags.writeable
    assert not sample.gradients.flags.writeable


def test_tilted_reversed_axis_strided_and_empty_positions() -> None:
    source_direction = np.array([2.0, -2.0, 1.0])
    field = AxialCoordinateField(source_direction)
    source_direction[:] = 99.0
    axis = np.array([2.0, -2.0, 1.0]) / 3.0
    stored_direction = field.direction.copy()
    points = np.arange(30.0).reshape(10, 3)[::2]

    values = field.sample(points)
    reversed_field = AxialCoordinateField(-stored_direction)
    reversed_values = reversed_field.sample(points)
    empty = field.sample_with_gradient(np.empty((0, 3)))

    np.testing.assert_allclose(values, points @ axis)
    np.testing.assert_allclose(reversed_values, -values)
    np.testing.assert_array_equal(field.direction, axis)
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)
    assert not empty.values.flags.writeable
    assert not empty.gradients.flags.writeable
