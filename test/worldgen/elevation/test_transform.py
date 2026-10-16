import numpy as np

from src.worldgen.elevation.transform import transform_strength


def test_transform_strength_zero_sign_and_homogeneity():
    normal = np.array([2.0, -2.0, 0.0, 2.0, 1.0])
    shear = np.array([1.0, 1.0, 2.0, -1.0, -1.0])

    strength = transform_strength(normal, shear)

    np.testing.assert_array_equal(strength, [2.0 / 3.0, -2.0 / 3.0, 0.0, -2.0, 0.0])
    np.testing.assert_array_equal(
        transform_strength(normal * 3.0, shear * 3.0), strength * 3.0
    )
