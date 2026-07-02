import numpy as np
import pyvista as pv


class Render:
    def __init__(
        self,
        vertex_array: np.ndarray,
        face_array: np.ndarray | None = None,
        dual_vertices: np.ndarray | None = None,
        dual_faces: list[list[int]] | None = None,
    ) -> None:
        self.vertex_array: np.ndarray = vertex_array
        self.face_array: np.ndarray | None = face_array
        self.dual_vertices: np.ndarray | None = dual_vertices
        self.dual_faces: list[list[int]] | None = dual_faces
        self.mesh: pv.PolyData | None = None

    def generate_mesh(self) -> pv.PolyData:
        if self.face_array is not None:
            n_faces = self.face_array.shape[0]
            faces = np.empty(n_faces * 4, dtype=np.int64)
            faces[::4] = 3
            faces[1::4] = self.face_array[:, 0]
            faces[2::4] = self.face_array[:, 1]
            faces[3::4] = self.face_array[:, 2]
            return pv.PolyData(self.vertex_array, faces)

        if self.dual_faces is not None:
            face_counts = [len(f) for f in self.dual_faces]
            flat = np.empty(sum(c + 1 for c in face_counts), dtype=np.int64)
            offset = 0
            for face in self.dual_faces:
                flat[offset] = len(face)
                flat[offset + 1:offset + 1 + len(face)] = face
                offset += 1 + len(face)
            return pv.PolyData(self.dual_vertices, flat)

        msg = "Provide either face_array (triangles) or dual_faces (polygons)."
        raise ValueError(msg)

    def display(self) -> None:
        self.mesh = self.generate_mesh()
        self.mesh.plot(show_edges=True, color="lightblue")
