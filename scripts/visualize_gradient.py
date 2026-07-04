"""Export mesh + gradient vectors to OBJ for visual inspection.

Usage:
    .venv/bin/python scripts/visualize_gradient.py
    # Then load output/gradient_test.obj in Blender, MeshLab, etc.
"""

import numpy as np
from src.core.geometry.mesh import Mesh
from src.core.field.vector.gradient import gradient
from src.core.field.scalar.noise import fbm


def write_mesh_and_vectors(
    path: str,
    vertices: np.ndarray,
    faces: np.ndarray,
    vectors: np.ndarray,
    scale: float = 0.05,
) -> None:
    """Write a mesh with vector arrows as line segments in OBJ format."""
    with open(path, "w") as f:
        f.write("# Gradient diagnostic mesh\n")
        f.write(f"o Mesh\n")

        # Vertex positions
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Arrow tip positions (vertex + scaled gradient)
        tip_offset = len(vertices)
        for i, v in enumerate(vertices):
            tip = v + vectors[i] * scale
            f.write(f"v {tip[0]:.6f} {tip[1]:.6f} {tip[2]:.6f}\n")

        # Faces (1-indexed)
        for face in faces:
            f.write(f"f {int(face[0])+1} {int(face[1])+1} {int(face[2])+1}\n")

        # Lines from each vertex to its arrow tip
        for i in range(len(vertices)):
            f.write(f"l {i+1} {tip_offset + i + 1}\n")


def main() -> None:
    mesh = Mesh(nu=10, radius=1.0)

    # Scalar field: FBM noise
    values = fbm(mesh.vertices, octaves=4, base_frequency=1.0)

    # Gradient (uphill)
    g = gradient(mesh.vertices, mesh.neighbors, values, descending=False)

    write_mesh_and_vectors(
        "output/gradient_test.obj",
        mesh.vertices,
        mesh.faces,
        g,
        scale=0.05,
    )
    print(f"Wrote output/gradient_test.obj")
    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces: {len(mesh.faces)}")


if __name__ == "__main__":
    main()
