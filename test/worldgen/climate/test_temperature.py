import numpy as np
import pytest

from src.worldgen.climate.temperature import TemperatureConfig
from src.worldgen.climate.temperature import LatitudeTemperatureField
from src.worldgen.field.axis import AxialCoordinateField


def test_temperature_equator_poles_and_hemispheric_symmetry():
    field = LatitudeTemperatureField(
        AxialCoordinateField(np.array([0.0, 0.0, 1.0])),
        TemperatureConfig(equator_temperature_c=30.0, pole_temperature_c=-20.0),
    )
    latitudes = np.deg2rad([-90.0, -60.0, -45.0, -30.0, 0.0, 30.0, 45.0, 60.0, 90.0])
    points = np.column_stack(
        (np.cos(latitudes), np.zeros(len(latitudes)), np.sin(latitudes))
    )
    values = field.sample(points)
    np.testing.assert_allclose(
        values, [-20.0, -7.5, 5.0, 17.5, 30.0, 17.5, 5.0, -7.5, -20.0]
    )
    np.testing.assert_array_equal(values, values[::-1])
    assert not values.flags.writeable


def test_temperature_is_volumetric_and_has_no_equatorial_seam():
    field = LatitudeTemperatureField(
        AxialCoordinateField(np.array([0.0, 0.0, 1.0])),
        TemperatureConfig(equator_temperature_c=40.0, pole_temperature_c=0.0),
    )
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [3.0, -4.0, 0.0],
            [0.0, 0.0, 2.0],
            [1.0, 0.0, -1e-6],
            [1.0, 0.0, 1e-6],
        ]
    )
    sample = field.sample_with_gradient(points)
    np.testing.assert_array_equal(sample.values[:3], [40.0, 40.0, -120.0])
    np.testing.assert_array_equal(
        sample.gradients[:3], [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, -160.0]]
    )
    np.testing.assert_array_equal(sample.values[3], sample.values[4])
    np.testing.assert_allclose(sample.gradients[3], -sample.gradients[4])
    np.testing.assert_allclose(sample.values[3:], 40.0, atol=1e-9, rtol=0.0)


def test_tilted_temperature_gradient_and_constant_temperature():
    axis = AxialCoordinateField(np.array([1.0, 2.0, 2.0]))
    field = LatitudeTemperatureField(axis, TemperatureConfig(24.0, -12.0))
    points = np.array(
        [[0.2, -0.3, 0.4], [1.2, 0.3, -0.1], [-0.5, 0.7, -1.3], [0.0, 0.0, 0.0]]
    )
    sample = field.sample_with_gradient(points)
    step = 1e-6
    numerical = np.column_stack(
        [
            (
                field.sample(points + offset * step)
                - field.sample(points - offset * step)
            )
            / (2.0 * step)
            for offset in np.eye(3)
        ]
    )
    np.testing.assert_allclose(sample.gradients, numerical, rtol=1e-7, atol=1e-8)
    np.testing.assert_array_equal(sample.values, field.sample(points))
    constant = LatitudeTemperatureField(
        axis, TemperatureConfig(-7.0, -7.0)
    ).sample_with_gradient(points)
    np.testing.assert_array_equal(constant.values, np.full(len(points), -7.0))
    np.testing.assert_array_equal(constant.gradients, np.zeros_like(points))
    assert not sample.values.flags.writeable
    assert not sample.gradients.flags.writeable


@pytest.mark.parametrize("axis_direction", [(0.0, 0.0, 1.0), (1.0, 2.0, -2.0)])
def test_temperature_is_independent_of_batch_layout_and_axis_scale(axis_direction):
    axis = AxialCoordinateField(np.array(axis_direction))
    field = LatitudeTemperatureField(axis, TemperatureConfig())
    points = np.random.default_rng(31).uniform(-1.5, 1.5, (17, 3))
    original = points.copy()
    points.setflags(write=False)
    whole = field.sample_with_gradient(points)
    for indices in (
        slice(None, None, 2),
        slice(0, 7),
        slice(7, None),
        np.arange(16, -1, -1),
    ):
        sample = field.sample_with_gradient(points[indices])
        np.testing.assert_array_equal(sample.values, whole.values[indices])
        np.testing.assert_array_equal(sample.gradients, whole.gradients[indices])
    reversed_axis = LatitudeTemperatureField(
        AxialCoordinateField(-2.0 * np.array(axis_direction)), TemperatureConfig()
    )
    np.testing.assert_array_equal(reversed_axis.sample(points), whole.values)
    np.testing.assert_array_equal(points, original)
    empty = field.sample_with_gradient(np.empty((0, 3)))
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)
    assert empty.values.dtype == empty.gradients.dtype == np.float64
    assert not empty.values.flags.writeable
    assert not empty.gradients.flags.writeable
