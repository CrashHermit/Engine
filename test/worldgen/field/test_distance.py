import numpy as np

from src.worldgen.field.distance import (
    multi_source_distances,
    nearest_source_distances,
    weighted_adjacency,
)
from src.worldgen.geometry.mesh import Mesh


def test_multi_source_distances_respect_labels_and_initial_distances() -> None:
    mesh = Mesh(
        np.array(
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]]
        ),
        np.array([[0, 1, 2], [0, 2, 3]]),
    )
    lengths = np.ones(len(mesh.edges))
    labels = np.array([0, 0, 0, 1])

    distances = multi_source_distances(
        mesh,
        np.array([0, 0, 3]),
        np.array([5.0, 2.0, 0.0]),
        lengths,
        labels,
    )

    np.testing.assert_array_equal(distances, [2.0, 3.0, 3.0, 0.0])


def test_multi_source_distances_leave_empty_sources_unreachable() -> None:
    mesh = Mesh(
        np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        np.array([[0, 1, 2]]),
    )

    distances = multi_source_distances(
        mesh,
        np.empty(0, dtype=np.int64),
        np.empty(0),
        np.ones(len(mesh.edges)),
        np.zeros(len(mesh.vertices), dtype=np.int64),
    )
    assert np.all(np.isinf(distances))


def test_arbitrary_edge_weights_are_rebuilt_for_each_distance_call() -> None:
    mesh = Mesh(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        np.array([[0, 1, 2]]),
    )
    first_lengths = np.array([2.0, 7.0, 3.0])
    second_lengths = np.array([11.0, 5.0, 13.0])

    first_adjacency = weighted_adjacency(mesh, first_lengths)
    second_adjacency = weighted_adjacency(mesh, second_lengths)
    assert first_adjacency[0] == [(1, 2.0), (2, 7.0)]
    assert second_adjacency[0] == [(1, 11.0), (2, 5.0)]

    sources = np.array([0])
    initial_distances = np.array([0.0])
    labels = np.zeros(len(mesh.vertices), dtype=np.int64)
    first_distances = multi_source_distances(
        mesh, sources, initial_distances, first_lengths, labels
    )
    second_distances = multi_source_distances(
        mesh, sources, initial_distances, second_lengths, labels
    )

    np.testing.assert_array_equal(first_distances, [0.0, 2.0, 5.0])
    np.testing.assert_array_equal(second_distances, [0.0, 11.0, 5.0])


def test_nearest_source_distances_ties_offsets_cutoff_and_regions() -> None:
    adjacency = [
        [(1, 1.0)],
        [(0, 1.0), (2, 1.0)],
        [(1, 1.0), (3, 1.0)],
        [(2, 1.0), (4, 1.0)],
        [(3, 1.0), (5, 1.0)],
        [(4, 1.0)],
    ]
    regions = np.array([0, 0, 0, 0, 0, 1])

    distances, source_ids = nearest_source_distances(
        adjacency,
        np.array([0, 0, 2]),
        np.array([0.5, 0.5, 0.5]),
        np.array([9, 8, 3]),
        regions,
        max_distance=1.5,
    )

    assert distances[0] == 0.5
    assert source_ids[0] == 8
    assert distances[2] == 0.5
    assert source_ids[2] == 3
    # Vertex 1 is equidistant from both sources; the smaller source ID wins.
    assert distances[1] == 1.5
    assert source_ids[1] == 3
    assert distances[3] == 1.5
    assert source_ids[3] == 3
    # The cutoff excludes vertex 4 and the region boundary excludes vertex 5.
    assert np.isinf(distances[4])
    assert np.isinf(distances[5])
    assert source_ids[4] == -1
    assert source_ids[5] == -1
