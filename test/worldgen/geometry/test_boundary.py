import numpy as np

from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geometry.boundary import (
    BoundaryNetwork,
    SphericalRegions,
    arc_distances,
)


def _mesh() -> Mesh:
    vertices, faces = generate_icosphere(2)
    return Mesh(vertices, faces)


def test_dual_regions_locate_centers_and_interior_polygon_points() -> None:
    mesh = _mesh()
    regions = SphericalRegions(mesh)
    np.testing.assert_array_equal(
        regions.locate(mesh.vertices), np.arange(len(mesh.vertices))
    )
    points = []
    owners = []
    for owner, face in enumerate(mesh.dual_faces):
        corner = mesh.dual_vertices[face[0]]
        points.append(
            (mesh.vertices[owner] * 3.0 + corner)
            / np.linalg.norm(mesh.vertices[owner] * 3.0 + corner)
        )
        owners.append(owner)
    np.testing.assert_array_equal(regions.locate(np.asarray(points)), owners)


def test_dual_polygon_shared_edge_and_junction_are_stable() -> None:
    mesh = _mesh()
    regions = SphericalRegions(mesh)
    face0, face1 = mesh.dual_faces[0][:2]
    shared_edge_midpoint = mesh.dual_vertices[face0] + mesh.dual_vertices[face1]
    shared_edge_midpoint /= np.linalg.norm(shared_edge_midpoint)
    # A dual vertex is a junction shared by the three cells of a primal face.
    junction = mesh.dual_vertices[face0]
    points = np.vstack((shared_edge_midpoint, junction))
    first = regions.locate(points)
    for _ in range(4):
        np.testing.assert_array_equal(regions.locate(points), first)
    assert first[0] in (0, *[int(v) for v in mesh.neighbors(0)])
    assert first[1] == int(np.min(mesh.faces[face0]))


def test_arc_distance_is_to_finite_minor_arc_including_endpoints() -> None:
    starts = np.array([[1.0, 0.0, 0.0]] * 3)
    ends = np.array([[0.0, 1.0, 0.0]] * 3)
    points = np.array(
        [
            [1.0, 1.0, 0.0],  # on arc
            [1.0, -1.0, 0.0],  # nearest endpoint
            [0.0, 0.0, 1.0],  # equidistant from the arc and both endpoints
        ]
    )
    distances, closest = arc_distances(points, starts, ends)
    np.testing.assert_allclose(distances, [0.0, 12.5, 25.0], atol=1e-12)
    np.testing.assert_allclose(closest[0], [2**-0.5, 2**-0.5, 0.0])
    np.testing.assert_allclose(closest[1], starts[1])
    np.testing.assert_allclose(closest[2], starts[2])


def test_boundary_network_index_matches_brute_force_and_candidates() -> None:
    mesh = _mesh()
    labels = np.arange(len(mesh.vertices)) % 3
    network = BoundaryNetwork(mesh, labels)
    rng = np.random.default_rng(91)
    points = rng.normal(size=(70, 3))
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    distances, ids, closest = network.nearest(points)
    for i, point in enumerate(points):
        all_distances, _ = arc_distances(point, network.starts, network.ends)
        brute = int(np.argmin(all_distances))
        np.testing.assert_allclose(distances[i], all_distances[brute], atol=1e-12)
        assert ids[i] == brute
        np.testing.assert_allclose(
            closest[i],
            arc_distances(point, network.starts[brute], network.ends[brute])[1],
        )
        candidates = network.candidates(point[None, :], distances[i] + 0.02)[0]
        expected = np.flatnonzero(all_distances <= distances[i] + 0.02 + 1e-12)
        assert np.isin(expected, candidates).all()


def test_spatial_queries_cover_poles_and_antimeridian() -> None:
    mesh = _mesh()
    regions = SphericalRegions(mesh)
    labels = np.arange(len(mesh.vertices)) % 2
    network = BoundaryNetwork(mesh, labels)
    points = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0], [-1.0, 0.0, 0.0]])

    owners = regions.locate(points)
    assert np.all((0 <= owners) & (owners < len(mesh.vertices)))
    distances, segment_ids, _ = network.nearest(points)
    for i, point in enumerate(points):
        brute, _ = arc_distances(point, network.starts, network.ends)
        assert distances[i] == np.min(brute)
        assert segment_ids[i] == int(np.argmin(brute))
        candidates = network.candidates(point[None, :], distances[i] + 1e-9)[0]
        assert np.isin(np.flatnonzero(brute <= distances[i] + 1e-9), candidates).all()


def test_boundary_network_preserves_requested_order_and_empty_results() -> None:
    mesh = _mesh()
    labels = np.arange(len(mesh.vertices)) % 2
    all_edges = np.flatnonzero(labels[mesh.edges[:, 0]] != labels[mesh.edges[:, 1]])
    ordered = all_edges[::-1]
    network = BoundaryNetwork(mesh, labels, ordered)
    np.testing.assert_array_equal(network.edge_indices, ordered)
    np.testing.assert_array_equal(network.left_labels, labels[mesh.edges[ordered, 0]])
    empty = BoundaryNetwork(mesh, np.zeros(len(mesh.vertices), dtype=np.int64))
    distance, segment, closest = empty.nearest(np.array([[1.0, 0.0, 0.0]]))
    assert np.isinf(distance[0])
    assert segment[0] == -1
    np.testing.assert_array_equal(closest, np.zeros((1, 3)))
    assert empty.candidates(np.array([[1.0, 0.0, 0.0]]), 1.0)[0].size == 0
