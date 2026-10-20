import numpy as np

from src.worldgen.geometry.voronoi import (
    build_voronoi_boundary_geometry,
    voronoi_boundary_distances,
)


def _distance(geometry, pair, positions):
    face_index = np.flatnonzero(np.all(geometry.region_pairs == pair, axis=1))[0]
    return voronoi_boundary_distances(positions, geometry)[:, face_index]


def test_two_seed_face_is_exact_bisector_and_seed_scale_does_not_set_width():
    positions = np.array(
        [[0.0, 0.0, 0.0], [0.25, 0.0, 0.0], [-0.25, 0.0, 0.0], [1.0, 0.0, 0.0]]
    )
    for seeds in (
        np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[-0.01, 0.0, 0.0], [0.01, 0.0, 0.0]]),
    ):
        geometry = build_voronoi_boundary_geometry(seeds)
        np.testing.assert_array_equal(geometry.region_pairs, [[0, 1]])
        np.testing.assert_allclose(
            _distance(geometry, [0, 1], positions), [0.0, 0.25, 0.25, 1.0]
        )
        assert geometry.region_pairs.dtype == np.int64
        assert not geometry.region_pairs.flags.writeable


def test_collinear_seeds_keep_only_adjacent_region_faces():
    seeds = np.array([[-1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    geometry = build_voronoi_boundary_geometry(seeds)

    np.testing.assert_array_equal(geometry.region_pairs, [[0, 1], [1, 2]])
    points = np.array([[-0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.5, 0.0, 0.0]])
    np.testing.assert_allclose(
        voronoi_boundary_distances(points, geometry),
        [[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]],
    )


def test_clipped_face_distance_includes_edges_and_is_continuous_at_edge():
    seeds = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    geometry = build_voronoi_boundary_geometry(seeds)
    points = np.array([[0.0, 1.0, 0.0], [0.1, 1.0, 0.0], [0.0, 0.75, 0.0]])

    np.testing.assert_allclose(
        _distance(geometry, [0, 1], points), [0.25, np.sqrt(0.0725), 0.0]
    )
    epsilon = 1e-5
    edge_samples = np.array([[0.0, 0.75 - epsilon, 0.0], [0.0, 0.75 + epsilon, 0.0]])
    np.testing.assert_allclose(
        _distance(geometry, [0, 1], edge_samples), [0.0, epsilon], atol=1e-12
    )
    np.testing.assert_allclose(
        voronoi_boundary_distances(points[2:3], geometry), np.zeros((1, 3))
    )


def test_lower_dimensional_contacts_are_not_reported_as_faces():
    seeds = np.array(
        [[-1.0, -1.0, 0.0], [1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [-1.0, 1.0, 0.0]]
    )

    geometry = build_voronoi_boundary_geometry(seeds)

    np.testing.assert_array_equal(
        geometry.region_pairs, [[0, 1], [0, 3], [1, 2], [2, 3]]
    )


def test_bounded_face_distance_includes_clipped_corner():
    seeds = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
    )
    geometry = build_voronoi_boundary_geometry(seeds)

    np.testing.assert_allclose(
        _distance(geometry, [0, 1], np.array([[0.5, 0.75, 0.75]])),
        [np.sqrt(0.125)],
    )


def test_empty_and_single_seed_geometry_have_typed_read_only_results():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    for seeds in (np.empty((0, 3)), np.array([[0.0, 0.0, 0.0]])):
        geometry = build_voronoi_boundary_geometry(seeds)
        distances = voronoi_boundary_distances(points, geometry)
        assert geometry.region_pairs.shape == (0, 2)
        assert geometry.region_pairs.dtype == np.int64
        assert distances.shape == (2, 0)
        assert distances.dtype == np.float64
        assert not geometry.region_pairs.flags.writeable
        assert not distances.flags.writeable

    geometry = build_voronoi_boundary_geometry(
        np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    )
    empty = voronoi_boundary_distances(np.empty((0, 3)), geometry)
    assert empty.shape == (0, 1)
    assert not empty.flags.writeable
