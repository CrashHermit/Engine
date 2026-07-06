import numpy as np
import pyvista as pv

from src.core.geometry.mesh import Mesh

class Render:
    def __init__(self, mesh: Mesh, plates: dict[int, int], velocity: np.ndarray) -> None:
        self.mesh = mesh
        self.plates = plates
        self.velocity = velocity
        self.pv_mesh = self._build_dual_polydata()
        self._attach_plate_data()

    def _build_dual_polydata(self) -> pv.PolyData:
        vertices = self.mesh.dual_vertices
        faces = self.mesh.dual_faces

        counts = [len(face) for face in faces]

        flat = np.empty(sum(count + 1 for count in counts), dtype=np.int64)
        offset = 0

        for face in faces:
            flat[offset] = len(face)
            flat[offset + 1 : offset + 1 + len(face)] = face
            offset += 1 + len(face)

        return pv.PolyData(vertices, flat)

    def _attach_plate_data(self) -> None:
        arr = np.full(len(self.mesh.dual_faces), -1, dtype=int)
        for vertex_index, plate_id in self.plates.items():
            arr[vertex_index] = plate_id

        self.pv_mesh.cell_data["plate_id"] = arr

    def show_plates(self, arrow_scale: float) -> None:
        plotter = pv.Plotter()
        plotter.add_mesh(mesh=self.pv_mesh, scalars="plate_id", cmap="tab10", show_edges=True, lighting=True)
        plotter.add_arrows(cent=self.mesh.vertices, direction=self.velocity, mag=arrow_scale, color="white", )
        plotter.show()




