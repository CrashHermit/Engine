import numpy as np

from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geometry.spherical import angular_distances
from src.worldgen.geometry.topology import boundary_components


def test_spherical_distance_and_edge_percentage() -> None:
    left = np.array([[1.0, 0.0, 0.0]])
    right = np.array([[0.0, 1.0, 0.0]])

    np.testing.assert_allclose(angular_distances(left, right), np.pi / 2.0)
    np.testing.assert_allclose(
        angular_distances(left, right) * 100.0 / (2.0 * np.pi), 25.0
    )


def test_mesh_metric_caches_have_known_lengths_and_immutable_adjacency() -> None:
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

    np.testing.assert_allclose(mesh.edge_lengths_percent, [25.0, 25.0, 25.0])
    assert mesh.edge_lengths_percent is mesh.edge_lengths_percent
    assert isinstance(mesh.geographic_adjacency, tuple)
    assert mesh.geographic_adjacency == (
        ((1, 25.0), (2, 25.0)),
        ((0, 25.0), (2, 25.0)),
        ((0, 25.0), (1, 25.0)),
    )
    assert mesh.geographic_adjacency is mesh.geographic_adjacency
    assert not mesh.edge_lengths_percent.flags.writeable
    with np.testing.assert_raises(ValueError):
        mesh.edge_lengths_percent[0] = 0.0
    with np.testing.assert_raises(TypeError):
        mesh.geographic_adjacency[0][0] = (1, 0.0)


def test_mesh_edge_face_incidence_and_neighbor_edge_csr_alignment() -> None:
    mesh = Mesh(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [-1.0, 0.0, 0.0],
            ]
        ),
        np.array([[0, 1, 2], [0, 2, 3]]),
    )

    expected_incidence = []
    for left, right in mesh.edges:
        expected_incidence.append(
            np.flatnonzero(
                np.any(
                    mesh.faces[:, :, None] == left,
                    axis=1,
                )
                & np.any(mesh.faces[:, :, None] == right, axis=1)
            )
        )
    assert isinstance(mesh.edge_face_indices, tuple)
    for actual, expected in zip(mesh.edge_face_indices, expected_incidence):
        np.testing.assert_array_equal(actual, expected)
        assert not actual.flags.writeable
    assert sorted(len(faces) for faces in mesh.edge_face_indices) == [1, 1, 1, 1, 2]

    for vertex, neighbors in enumerate(mesh.geographic_adjacency):
        start, end = mesh.neighbor_offsets[vertex : vertex + 2]
        assert len(neighbors) == end - start
        for offset, (neighbor, weight) in enumerate(neighbors, start=int(start)):
            assert neighbor == mesh.neighbor_indices[offset]
            edge = np.flatnonzero(
                np.all(mesh.edges == np.sort([vertex, neighbor]), axis=1)
            )
            assert len(edge) == 1
            edge_index = int(edge[0])
            assert mesh.neighbor_edge_indices[offset] == edge_index
            reverse_start, reverse_end = mesh.neighbor_offsets[neighbor : neighbor + 2]
            reverse_offsets = np.flatnonzero(
                mesh.neighbor_indices[reverse_start:reverse_end] == vertex
            )
            assert len(reverse_offsets) == 1
            assert (
                mesh.neighbor_edge_indices[int(reverse_start) + int(reverse_offsets[0])]
                == edge_index
            )
            np.testing.assert_allclose(weight, mesh.edge_lengths_percent[edge_index])
            assert (vertex, weight) in mesh.geographic_adjacency[neighbor]
    assert not mesh.neighbor_edge_indices.flags.writeable


def test_separate_meshes_keep_separate_metric_data() -> None:
    vertices = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    first = Mesh(vertices, np.array([[0, 1, 2]]))
    second = Mesh(vertices, np.array([[0, 1, 2]]))

    assert first.edge_lengths_percent is not second.edge_lengths_percent
    assert first.geographic_adjacency is not second.geographic_adjacency


def test_boundary_components_follow_shared_primal_faces_and_labels() -> None:
    mesh = Mesh(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [-1.0, 0.0, 0.0],
            ]
        ),
        np.array([[0, 1, 2], [0, 2, 3]]),
    )
    edge_indices = np.array([0, 3, 4])
    labels = np.array([[1, 2], [1, 2], [1, 2]])

    components = boundary_components(mesh, edge_indices, labels)

    np.testing.assert_array_equal(components, [0, 0, 1])
    assert all(len(faces) >= 1 for faces in mesh.edge_face_indices)


def test_boundary_components_split_changed_labels_and_handle_empty() -> None:
    vertices, faces = generate_icosphere(2)
    mesh = Mesh(vertices, faces)
    selected = np.array([0, 1, 2])
    labels = np.array([[1, 2], [1, 3], [1, 2]])

    components = boundary_components(mesh, selected, labels)

    assert components.shape == (3,)
    np.testing.assert_array_equal(
        boundary_components(
            mesh, np.empty(0, dtype=np.int64), np.empty((0, 2), dtype=np.int64)
        ),
        np.empty(0, dtype=np.int64),
    )
    assert len(mesh.edge_lengths_percent) == len(mesh.edges)
