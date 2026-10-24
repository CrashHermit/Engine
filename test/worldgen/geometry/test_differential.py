import numpy as np

from src.worldgen.geometry.differential import (
    pullback_covectors,
    pullback_normals,
    pullback_vectors,
    pushforward_covectors,
    pushforward_normal_jacobians,
    pushforward_normals,
    pushforward_vector_jacobians,
    pushforward_vectors,
)


def test_vector_covector_transport_round_trips_and_preserves_pairing():
    jacobians = np.array(
        [
            [[1.0, 0.6, -0.2], [0.0, 1.0, 0.3], [0.0, 0.0, 1.0]],
            [[0.8, 0.0, 0.1], [0.2, 1.2, 0.0], [0.0, -0.3, 1.1]],
        ]
    )
    vectors = np.array([[2.0, -3.0, 1.0], [-0.2, 0.8, 0.6]])
    covectors = np.array([[0.2, 0.7, -0.4], [1.0, -0.3, 0.2]])
    output_vectors = pushforward_vectors(vectors, jacobians)
    output_covectors = pushforward_covectors(covectors, jacobians)
    np.testing.assert_allclose(
        pullback_vectors(output_vectors, jacobians), vectors, atol=1e-14
    )
    np.testing.assert_allclose(
        pullback_covectors(output_covectors, jacobians), covectors, atol=1e-14
    )
    np.testing.assert_allclose(
        np.einsum("ni,ni->n", output_vectors, output_covectors),
        np.einsum("ni,ni->n", vectors, covectors),
        atol=1e-14,
    )
    normals = covectors / np.linalg.norm(covectors, axis=1, keepdims=True)
    np.testing.assert_allclose(
        pullback_normals(pushforward_normals(normals, jacobians), jacobians),
        normals,
        atol=1e-14,
    )
    paired = np.stack((vectors, -vectors), axis=1)
    np.testing.assert_allclose(
        pullback_vectors(
            pushforward_vectors(paired, jacobians[:, None]), jacobians[:, None]
        ),
        paired,
        atol=1e-14,
    )


def test_transport_accepts_empty_queries_without_mutable_outputs():
    vectors = np.empty((0, 3))
    jacobians = np.empty((0, 3, 3))
    for transform in (
        pushforward_vectors,
        pullback_vectors,
        pushforward_covectors,
        pullback_covectors,
        pushforward_normals,
        pullback_normals,
    ):
        output = transform(vectors, jacobians)
        assert output.shape == (0, 3)
        assert not output.flags.writeable


def test_transported_vector_and_normal_jacobians_match_analytic_diagnostics():
    points = np.array([[0.2, -0.3, 0.4], [-0.1, 0.5, 0.2]])
    jacobians = np.broadcast_to(
        np.array([[1.1, 0.2, 0.0], [-0.1, 0.9, 0.1], [0.0, 0.2, 1.2]]),
        (len(points), 3, 3),
    ).copy()
    hessians = np.zeros((len(points), 3, 3, 3))
    hessians[:, 0, 0, 1] = hessians[:, 0, 1, 0] = 0.3
    hessians[:, 2, 1, 2] = hessians[:, 2, 2, 1] = -0.2
    vector = np.column_stack((1 + points[:, 1], points[:, 0] ** 2, points[:, 2]))
    vector_jacobian = np.zeros((len(points), 3, 3))
    vector_jacobian[:, 0, 1] = 1.0
    vector_jacobian[:, 1, 0] = 2 * points[:, 0]
    vector_jacobian[:, 2, 2] = 1.0
    pushed_jacobian = pushforward_vector_jacobians(
        vector, vector_jacobian, jacobians, hessians
    )
    normals = np.broadcast_to([0.3, 0.4, 0.8], (len(points), 3)).copy()
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    normal_jacobian = np.zeros((len(points), 3, 3))
    normal_jacobian[:, 0, 0] = 0.2
    normal_jacobian[:, 1, 1] = -0.1
    pushed_normal_jacobian = pushforward_normal_jacobians(
        normals, normal_jacobian, jacobians, hessians
    )
    assert pushed_jacobian.shape == (len(points), 3, 3)
    transported_normals = pushforward_normals(normals, jacobians)
    np.testing.assert_allclose(
        np.einsum("ni,nik->nk", transported_normals, pushed_normal_jacobian),
        0.0,
        atol=1e-14,
    )
    assert not pushed_normal_jacobian.flags.writeable
    paired_jacobian = pushforward_vector_jacobians(
        vector,
        vector_jacobian,
        np.broadcast_to(jacobians[:, None], (2, 3, 3, 3)),
        np.broadcast_to(hessians[:, None], (2, 3, 3, 3, 3)),
    )
    assert paired_jacobian.shape == (2, 3, 3, 3)
    paired_normal_jacobian = pushforward_normal_jacobians(
        normals,
        normal_jacobian,
        np.broadcast_to(jacobians[:, None], (2, 3, 3, 3)),
        np.broadcast_to(hessians[:, None], (2, 3, 3, 3, 3)),
    )
    assert paired_normal_jacobian.shape == (2, 3, 3, 3)


def test_pushforward_derivative_helpers_match_finite_difference_diagnostics():
    points = np.array([[0.2, -0.3, 0.4]])

    def map_jacobian(query):
        x, y, z = query.T
        values = np.broadcast_to(
            [[1.1, 0.2, 0.0], [-0.1, 0.9, 0.1], [0.0, 0.2, 1.2]],
            (len(query), 3, 3),
        ).copy()
        values[:, 0, 0] += 0.3 * y
        values[:, 0, 1] += 0.3 * x
        values[:, 2, 1] -= 0.2 * z
        values[:, 2, 2] -= 0.2 * y
        return values

    map_hessian = np.zeros((1, 3, 3, 3))
    map_hessian[:, 0, 0, 1] = map_hessian[:, 0, 1, 0] = 0.3
    map_hessian[:, 2, 1, 2] = map_hessian[:, 2, 2, 1] = -0.2
    vector = np.column_stack((1 + points[:, 1], points[:, 0] ** 2, points[:, 2]))
    vector_jacobian = np.zeros((1, 3, 3))
    vector_jacobian[:, 0, 1] = 1.0
    vector_jacobian[:, 1, 0] = 2 * points[:, 0]
    vector_jacobian[:, 2, 2] = 1.0
    analytic_vector = pushforward_vector_jacobians(
        vector, vector_jacobian, map_jacobian(points), map_hessian
    )

    def transported_vector(query):
        source = np.column_stack((1 + query[:, 1], query[:, 0] ** 2, query[:, 2]))
        return pushforward_vectors(source, map_jacobian(query))

    raw_normal = np.column_stack(
        (0.3 + 0.2 * points[:, 0], 0.4 - 0.1 * points[:, 1], 0.8 + points[:, 2] * 0)
    )
    raw_normal_jacobian = np.zeros((1, 3, 3))
    raw_normal_jacobian[:, 0, 0] = 0.2
    raw_normal_jacobian[:, 1, 1] = -0.1
    lengths = np.linalg.norm(raw_normal, axis=1, keepdims=True)
    normals = raw_normal / lengths
    normal_jacobian = (
        (np.eye(3) - normals[:, :, None] * normals[:, None, :])
        @ raw_normal_jacobian
        / lengths[:, :, None]
    )
    analytic_normal = pushforward_normal_jacobians(
        normals, normal_jacobian, map_jacobian(points), map_hessian
    )

    def transported_normal(query):
        raw = np.column_stack(
            (0.3 + 0.2 * query[:, 0], 0.4 - 0.1 * query[:, 1], 0.8 + query[:, 2] * 0)
        )
        raw /= np.linalg.norm(raw, axis=1, keepdims=True)
        return pushforward_normals(raw, map_jacobian(query))

    epsilon = 1e-5
    vector_finite = np.column_stack(
        [
            (
                transported_vector(points + np.eye(3)[axis] * epsilon)
                - transported_vector(points - np.eye(3)[axis] * epsilon)
            )[0]
            / (2 * epsilon)
            for axis in range(3)
        ]
    )
    normal_finite = np.column_stack(
        [
            (
                transported_normal(points + np.eye(3)[axis] * epsilon)
                - transported_normal(points - np.eye(3)[axis] * epsilon)
            )[0]
            / (2 * epsilon)
            for axis in range(3)
        ]
    )
    np.testing.assert_allclose(analytic_vector[0], vector_finite, atol=2e-9)
    np.testing.assert_allclose(analytic_normal[0], normal_finite, atol=2e-9)
