import numpy as np

from src.worldgen.field.compose import (
    SumScalarField,
    WarpedNormalField,
    WarpedScalarField,
    WarpedVectorField,
)
from src.worldgen.field.differential import ScalarSample, VectorSample


def _shear(points):
    return points @ np.array([[1.0, 2.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]).T


def _shear_with_jacobian(points):
    matrix = np.array([[1.0, 2.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    return VectorSample(_shear(points), np.broadcast_to(matrix, (len(points), 3, 3)))


def _quadratic(points):
    return points[:, 0] ** 2 + 3.0 * points[:, 1] * points[:, 2]


def _quadratic_with_gradient(points):
    return ScalarSample(
        _quadratic(points),
        np.column_stack((2.0 * points[:, 0], 3.0 * points[:, 2], 3.0 * points[:, 1])),
    )


def test_scalar_chain_rule_uses_transpose_and_keeps_world_space_addition_unwarped():
    field = WarpedScalarField(
        _shear, _quadratic, _shear_with_jacobian, _quadratic_with_gradient
    )
    variation = lambda points: points[:, 2] ** 2
    variation_gradient = lambda points: ScalarSample(
        variation(points),
        np.column_stack((np.zeros((len(points), 2)), 2.0 * points[:, 2])),
    )
    total = SumScalarField(
        (field.sample, variation), (field.sample_with_gradient, variation_gradient)
    )
    points = np.array([[1.0, 2.0, 3.0], [-0.3, 0.7, -0.2]])
    sample = total.sample_with_gradient(points)
    x, y, z = points.T
    np.testing.assert_allclose(sample.values, (x + 2 * y) ** 2 + 3 * y * z + z**2)
    np.testing.assert_allclose(
        sample.gradients,
        np.column_stack((2 * (x + 2 * y), 4 * (x + 2 * y) + 3 * z, 3 * y + 2 * z)),
    )
    assert not sample.gradients.flags.writeable
    empty = total.sample_with_gradient(np.empty((0, 3)))
    assert empty.values.shape == (0,)
    assert empty.gradients.shape == (0, 3)


def test_vector_and_normal_transport_preserves_tangency_under_shear():
    vectors = WarpedVectorField(
        _shear_with_jacobian,
        lambda points: np.broadcast_to([0.0, 1.0, 0.0], points.shape),
    )
    normals = WarpedNormalField(
        _shear_with_jacobian,
        lambda points: np.broadcast_to([1.0, 0.0, 0.0], points.shape),
    )
    points = np.array([[0.2, 0.4, 0.7], [-1.0, 0.0, 0.0]])
    np.testing.assert_allclose(vectors.sample(points), [[-2, 1, 0], [-2, 1, 0]])
    np.testing.assert_allclose(
        normals.sample(points), np.tile([1, 2, 0], (2, 1)) / np.sqrt(5)
    )
    np.testing.assert_allclose(
        np.einsum("ni,ni->n", vectors.sample(points), normals.sample(points)), 0.0
    )
