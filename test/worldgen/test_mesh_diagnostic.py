"""Diagnose holes in frequency_icosphere mesh output."""

import numpy as np
import pytest

from src.core.geometry.mesh import Mesh


def _write_obj(vertices: np.ndarray, faces: np.ndarray, path: str) -> None:
    """Write vertices and faces to Wavefront OBJ for inspection."""
    with open(path, "w") as f:
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for face in faces:
            # OBJ uses 1-based indexing
            f.write(f"f {int(face[0])+1} {int(face[1])+1} {int(face[2])+1}\n")


def _count_edge_occurrences(faces: np.ndarray) -> dict[tuple[int, int], int]:
    """Count how many faces share each undirected edge."""
    edge_counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for i in range(3):
            a, b = min(int(face[i]), int(face[(i + 1) % 3])), max(int(face[i]), int(face[(i + 1) % 3]))
            edge_counts[(a, b)] = edge_counts.get((a, b), 0) + 1
    return edge_counts


def test_mesh_triangle_count_matches_subdivision(nu: int = 10) -> None:
    """Verify triangle count matches expected 20 * nu^2 for a subdivided icosahedron."""
    mesh = Mesh(subdivisions=5)
    vertices, faces = mesh.generate_frequency_icosphere(nu=nu, radius=2.0)

    expected_triangles = 20 * nu * nu  # icosahedron has 20 faces, each subdivided into nu^2
    actual_triangles = faces.shape[0]

    print(f"  vertices: {vertices.shape[0]}")
    print(f"  faces: {actual_triangles}")
    print(f"  expected triangles: {expected_triangles}")
    print(f"  expected vertices (approx): 10 + 62*{nu} ≈ {10 + 62 * nu}")

    assert actual_triangles == expected_triangles, (
        f"Triangle mismatch: expected {expected_triangles}, got {actual_triangles}"
    )


def test_mesh_no_invalid_face_references(nu: int = 10) -> None:
    """All face vertex indices must be within range."""
    mesh = Mesh(subdivisions=5)
    vertices, faces = mesh.generate_frequency_icosphere(nu=nu, radius=2.0)

    n_vertices = vertices.shape[0]
    max_index = int(faces.max())

    print(f"  max face index: {max_index}, vertex count: {n_vertices}")
    assert max_index < n_vertices, f"Face index {max_index} >= vertex count {n_vertices}"
    assert int(faces.min()) >= 0, f"Negative face index found"


def test_mesh_edge_manifold(nu: int = 10) -> None:
    """Every edge must be shared by exactly 2 faces (manifold) or 1 face (boundary)."""
    mesh = Mesh(subdivisions=5)
    vertices, faces = mesh.generate_frequency_icosphere(nu=nu, radius=2.0)

    edge_counts = _count_edge_occurrences(faces)

    boundary_edges = {k: v for k, v in edge_counts.items() if v == 1}
    double_edges = {k: v for k, v in edge_counts.items() if v == 2}
    triple_edges = {k: v for k, v in edge_counts.items() if v > 2}

    print(f"  total unique edges: {len(edge_counts)}")
    print(f"  boundary edges (count=1): {len(boundary_edges)}")
    print(f"  manifold edges (count=2): {len(double_edges)}")
    print(f"  overlapping edges (count>2): {len(triple_edges)}")

    assert len(triple_edges) == 0, (
        f"{len(triple_edges)} edges shared by 3+ faces — geometry overlap detected"
    )

    # A closed icosphere should have NO boundary edges
    assert len(boundary_edges) == 0, (
        f"{len(boundary_edges)} boundary edges found — mesh has holes/gaps"
    )


def test_mesh_export_obj(nu: int = 5) -> None:
    """Export to OBJ for visual inspection."""
    mesh = Mesh(subdivisions=5)
    vertices, faces = mesh.generate_frequency_icosphere(nu=nu, radius=2.0)
    _write_obj(vertices, faces, "output/icosphere_test.obj")
    print(f"  Wrote output/icosphere_test.obj ({vertices.shape[0]} verts, {faces.shape[0]} faces)")
