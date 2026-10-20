import numpy as np

from src.worldgen.elevation.shear import shear_strength
from src.worldgen.elevation.transform import transform_strength


def test_transform_strength_zero_sign_and_homogeneity():
    normal = np.array([2.0, -2.0, 0.0, 2.0, 1.0])
    shear = np.array([1.0, 1.0, 2.0, -1.0, -1.0])

    strength = transform_strength(normal, shear)

    np.testing.assert_array_equal(strength, [2.0 / 3.0, -2.0 / 3.0, 0.0, -2.0, 0.0])
    np.testing.assert_array_equal(
        transform_strength(normal * 3.0, shear * 3.0), strength * 3.0
    )


def test_shear_strength_partitions_shear_from_oblique_transform():
    normal = np.array([0.0, 2.0, -2.0, 1.0])
    shear = np.array([2.0, 2.0, 2.0, 0.5])

    pure_shear = shear_strength(normal, shear)
    oblique = transform_strength(normal, shear)

    np.testing.assert_array_equal(pure_shear, [2.0, 1.0, 1.0, 1.0 / 6.0])
    np.testing.assert_allclose(np.abs(oblique) + pure_shear, shear)
    assert pure_shear[0] == shear[0]
    assert pure_shear[3] < shear[3]
