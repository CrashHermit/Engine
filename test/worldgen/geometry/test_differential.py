import numpy as np

from src.worldgen.geometry.differential import (
    pullback_covectors,
    pullback_normals,
    pullback_vectors,
    pushforward_covectors,
    pushforward_normals,
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
