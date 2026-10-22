import numpy as np

from src.worldgen.elevation.shear import shear_strength
from src.worldgen.elevation.transform import transform_strength


def test_motion_responses_preserve_sign_zero_and_shear_budget():
    normal = np.array([0.0, 2.0, -2.0, 1.0, -1.0])
    shear = np.array([0.0, 2.0, 2.0, 0.5, 0.5])
    transform = transform_strength(normal, shear, smoothing=0.01)
    pure_shear = shear_strength(normal, shear, smoothing=0.01)

    assert transform[0] == pure_shear[0] == 0.0
    np.testing.assert_array_equal(np.sign(transform[1:]), np.sign(normal[1:]))
    np.testing.assert_allclose(
        transform_strength(-normal, shear, smoothing=0.01), -transform
    )
    np.testing.assert_allclose(
        shear_strength(-normal, shear, smoothing=0.01), pure_shear
    )
    assert np.all(pure_shear >= 0.0)
    assert np.all(np.abs(transform) + pure_shear <= shear)
    assert 0.0 < shear_strength(np.zeros(1), np.ones(1), smoothing=0.01)[0] <= 1.0


def test_fault_strengths_have_matching_derivatives_at_zero_normal_motion():
    delta = 1e-7
    normal = np.array([-delta, 0.0, delta])
    shear = np.ones(3)
    for response in (transform_strength, shear_strength):
        values = response(normal, shear, smoothing=0.01)
        left, right = np.diff(values) / delta
        np.testing.assert_allclose(left, right, atol=1e-4)
    assert transform_strength(normal, shear, smoothing=0.01)[0] < 0.0
    assert transform_strength(normal, shear, smoothing=0.01)[2] > 0.0


def test_fault_responses_join_smoothly_at_zero_tangential_and_total_motion():
    from src.worldgen.geometry.vector import relative_motion_components

    step = 1e-7
    offsets = np.array([-step, 0.0, step])
    normals = np.tile([1.0, 0.0, 0.0], (3, 1))
    for normal in (np.ones(3), offsets):
        velocity = np.column_stack((normal, offsets, np.zeros(3)))
        opening, shear = relative_motion_components(np.zeros((3, 3)), velocity, normals)
        for response in (transform_strength, shear_strength):
            values = response(opening, shear, smoothing=0.01)
            assert values[1] == 0.0
            np.testing.assert_allclose(np.diff(values) / step, 0.0, atol=1e-5)
