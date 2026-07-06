"""Diagnose holes in frequency_icosphere mesh output."""

import numpy as np
import pytest

from src.core.geometry.mesh import generate_icosphere


def _count_edge_occurrences(faces: np.ndarray) -> dict[tuple[int, int], int]:
    """Count how many faces share each undirected edge."""
    edge_counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for i in range(3):
            a, b = (
                min(int(face[i]), int(face[(i + 1) % 3])),
                max(int(face[i]), int(face[(i + 1) % 3])),
            )
            edge_counts[(a, b)] = edge_counts.get((a, b), 0) + 1
    return edge_counts


def test_mesh_triangle_count_matches_subdivision(nu: int = 10) -> None:
    """Verify triangle count matches expected 20 * nu^2 for a subdivided icosahedron."""
    vertices, faces = generate_icosphere(nu=nu)

    expected_triangles = (
        20 * nu * nu
    )  # icosahedron has 20 faces, each subdivided into nu^2
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
    vertices, faces = generate_icosphere(nu=nu)

    n_vertices = vertices.shape[0]
    max_index = int(faces.max())

    print(f"  max face index: {max_index}, vertex count: {n_vertices}")
    assert max_index < n_vertices, (
        f"Face index {max_index} >= vertex count {n_vertices}"
    )
    assert int(faces.min()) >= 0, f"Negative face index found"


def test_mesh_edge_manifold(nu: int = 10) -> None:
    """Every edge must be shared by exactly 2 faces (manifold) or 1 face (boundary)."""
    vertices, faces = generate_icosphere(nu=nu)

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


@pytest.mark.parametrize("nu", [2, 5, 10, 15, 20, 30, 60])
def test_generate_icosphere_speed(nu: int) -> None:
    """generate_icosphere must complete within a reasonable time."""
    import time

    start: float = time.perf_counter()
    generate_icosphere(nu=nu)
    elapsed: float = time.perf_counter() - start

    print(f"  nu={nu}: {elapsed*1000:.1f}ms")
    assert elapsed < 1.0, f"nu={nu} took {elapsed:.2f}s — too slow"
