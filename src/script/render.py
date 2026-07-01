import pyvista as pv
import numpy as np


class Render:
    def __init__(self, vertex_array: np.ndarray, face_array: np.ndarray) -> None:
        self.vertex_array: np.ndarray = vertex_array
        self.face_array: np.ndarray = face_array
        self.mesh: pv.PolyData = self.generate_mesh()

    def generate_mesh(self) -> pv.PolyData:
        # pyvista expects faces in connectivity format: [3, v0, v1, v2, 3, v3, v4, v5, ...]
        n_faces = self.face_array.shape[0]
        faces = np.empty(n_faces * 4, dtype=np.int64)
        faces[::4] = 3  # triangle marker
        faces[1::4] = self.face_array[:, 0]
        faces[2::4] = self.face_array[:, 1]
        faces[3::4] = self.face_array[:, 2]
        mesh = pv.PolyData(self.vertex_array, faces)

        return mesh

    def display(self) -> None:
        if self.mesh is None:
            self.generate_mesh()

        self.mesh.plot(show_edges=True, color="lightblue")
