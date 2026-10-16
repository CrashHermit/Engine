import numpy as np

from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geometry.spherical import angular_distances, edge_lengths_percent
from src.worldgen.geometry.topology import boundary_components, edge_face_indices


def test_spherical_distance_and_edge_percentage() -> None:
    left = np.array([[1.0, 0.0, 0.0]])
    right = np.array([[0.0, 1.0, 0.0]])

    np.testing.assert_allclose(angular_distances(left, right), np.pi / 2.0)
    np.testing.assert_allclose(
        angular_distances(left, right) * 100.0 / (2.0 * np.pi), 25.0
    )


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
    assert all(len(faces) >= 1 for faces in edge_face_indices(mesh))


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
    assert len(edge_lengths_percent(mesh)) == len(mesh.edges)
