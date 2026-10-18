import numpy as np

from src.worldgen.geometry.spherical import angular_distances, spherical_ring


def test_spherical_ring_is_unit_spaced_at_poles_and_antimeridian() -> None:
    near_antimeridian = np.array([-1.0, 1e-10, 0.0])
    near_antimeridian /= np.linalg.norm(near_antimeridian)
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            near_antimeridian,
        ]
    )
    angular_radius = 0.01 * 2.0 * np.pi

    ring = spherical_ring(positions, angular_radius)

    assert ring.shape == (len(positions), 8, 3)
    np.testing.assert_allclose(np.linalg.norm(ring, axis=2), 1.0, atol=1e-12)
    centers = np.repeat(positions, 8, axis=0)
    np.testing.assert_allclose(
        angular_distances(centers, ring.reshape(-1, 3)),
        angular_radius,
        atol=1e-12,
    )
    for points in ring:
        assert np.unique(points, axis=0).shape == (8, 3)

    np.testing.assert_allclose(
        ring[:, :4] + ring[:, 4:],
        np.broadcast_to(
            2.0 * np.cos(angular_radius) * positions[:, None, :],
            ring[:, :4].shape,
        ),
        atol=1e-12,
    )


def test_spherical_ring_is_independent_of_batch_order_and_handles_empty_input() -> None:
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    angular_radius = 0.2
    expected = spherical_ring(positions, angular_radius)
    order = np.array([2, 0, 1])

    np.testing.assert_array_equal(
        spherical_ring(positions[order], angular_radius), expected[order]
    )
    np.testing.assert_array_equal(
        spherical_ring(positions[[1]], angular_radius), expected[[1]]
    )
    assert spherical_ring(np.empty((0, 3)), angular_radius).shape == (0, 8, 3)
