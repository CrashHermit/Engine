import numpy as np


class Mesh:
    def __init__(self, subdivisions: int) -> None:
        self.subdivisions: int = subdivisions
        self.vertex_map: dict[tuple[float, float, float], int] = {}
        self.final_vertices: list[np.ndarray] = []
        self.final_faces: list[list[int]] = []

    def _add_vertex(self, vertex_coordinates: np.ndarray, radius: float) -> int:
        normalized_vertex = vertex_coordinates / np.linalg.norm(vertex_coordinates)
        key = tuple(np.round(normalized_vertex, 6))

        if key not in self.vertex_map:
            self.vertex_map[key] = len(self.final_vertices)
            self.final_vertices.append(normalized_vertex * radius)

        vertex_index = self.vertex_map[key]
        return vertex_index

    def _get_base_icosahedron(self) -> tuple[np.ndarray, np.ndarray]:
        phi = (1.0 + np.sqrt(5.0)) / 2.0

        base_vertices = np.array([
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
        ])

        base_faces = np.array([
            [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [0, 11, 5],
            [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [3, 9, 4],
            [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
            [1, 9, 5], [5, 9, 4]
        ])
        
        return base_vertices, base_faces

    def _subdivide_face_grid(self, face: np.ndarray, base_vertices: np.ndarray, nu: int, radius: float) -> dict[tuple[int, int], int]:
        a = base_vertices[face[0]]
        b = base_vertices[face[1]]
        c = base_vertices[face[2]]

        grid: dict[tuple[int, int], int] = {}
        for i in range(nu + 1):
            for j in range(nu + 1 - i):
                k: int = nu - i - j
                vertex_coordinates: np.ndarray = ((i * a) + (j * b) + (k * c)) / nu
                grid[(i, j)] = self._add_vertex(vertex_coordinates=vertex_coordinates, radius=radius)
        return grid

    def _stitch_face_triangles(self, grid: dict[tuple[int, int], int], nu: int) -> None:
        for i in range(nu):
            for j in range(nu - i):
                self.final_faces.append([grid[(i, j)], grid[(i+1, j)], grid[(i, j+1)]])

                if j < nu - i - 1:
                    self.final_faces.append([grid[(i+1, j)], grid[(i+1, j+1)], grid[(i, j+1)]])

    def generate_frequency_icosphere(self, nu: int, radius: float) -> tuple[np.ndarray, np.ndarray]:
        base_vertices, base_faces = self._get_base_icosahedron()

        for face in base_faces:
            grid = self._subdivide_face_grid(face, base_vertices, nu, radius)
            self._stitch_face_triangles(grid, nu)

        final_vertices_array: np.ndarray = np.array(self.final_vertices)
        final_faces_array: np.ndarray = np.array(self.final_faces)
        
        return final_vertices_array, final_faces_array

