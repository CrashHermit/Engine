import numpy as np
import pyvista as pv

from src.core.geometry.mesh import Mesh

class Render:
    def __init__(self, mesh: Mesh, plates: dict[int, int], plate_velocity: np.ndarray, plate_region_boundaries: dict[int, list[int]]) -> None:
        self.mesh = mesh
        self.plates = plates
        self.plate_velocity = plate_velocity
        self.plate_region_boundaries = plate_region_boundaries
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

    def _build_edge_face_map(self) -> dict[tuple[int, int], list[int]]:
        edge_faces: dict[tuple[int, int], list[int]] = {}
        for face_index, face in enumerate(self.mesh.faces):
            a: int = int(face[0])
            b: int = int(face[1])
            c: int = int(face[2])
            for edge in [(a, b), (b, c), (c, a)]:
                key = (min(edge), max(edge))
                edge_faces.setdefault(key, []).append(face_index)
        return edge_faces

    def _boundary_hex_lines(self) -> np.ndarray:                                                                                                                                               
       """Convert plate boundaries to hex-edge line segments."""                                                                                                                              
       dual_vertices = self.mesh.dual_vertices                                                                                                                                                
       edge_face_map = self._build_edge_face_map()                                                                                                                                            
       segments: list[np.ndarray] = []                                                                                                                                                        
       seen: set[tuple[int, int]] = set()                                                                                                                                                     
                                                                                                                                                                                              
       for u, neighbors in self.plate_region_boundaries.items():                                                                                                                                     
           for v in neighbors:                                                                                                                                                                
               key = (min(u, v), max(u, v))                                                                                                                                                   
               if key in seen:                                                                                                                                                                
                   continue                                                                                                                                                                   
               seen.add(key)                                                                                                                                                                  
                                                                                                                                                                                              
               faces = edge_face_map.get(key, [])                                                                                                                                             
               if len(faces) >= 2:                                                                                                                                                            
                   # The two triangle centroids = the hex boundary edge                                                                                                                       
                   segments.append(dual_vertices[faces[0]])                                                                                                                                   
                   segments.append(dual_vertices[faces[1]])                                                                                                                                   
                                                                                                                                                                                              
       return np.array(segments) 

    def _boundary_lines(self) -> np.ndarray:
        vertices = self.mesh.vertices
        segments: list[np.ndarray] = []
        seen: set[tuple[int, int]] = set()

        for cell, neighbors in self.plate_region_boundaries.items():
            for neighbor in neighbors:
                if (cell, neighbor) not in seen and (neighbor, cell) not in seen:
                    seen.add((cell, neighbor))
                    segments.append(vertices[cell])
                    segments.append(vertices[neighbor])

        return np.array(segments)
        

    def show_plates(self, arrow_scale: float) -> None:
        plotter = pv.Plotter()
        plotter.add_mesh(mesh=self.pv_mesh, scalars="plate_id", cmap="tab10", show_edges=True, lighting=True)
        plotter.add_arrows(cent=self.mesh.vertices, direction=self.plate_velocity, mag=arrow_scale, color="white", )
        if self.plate_region_boundaries is not None:
            lines = self._boundary_hex_lines()
            if len(lines) > 0:
                plotter.add_lines(lines, color="black", width=6)
        plotter.show()




