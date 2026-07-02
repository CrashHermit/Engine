import numpy as np


class Mesh:
    def __init__(self, subdivisions: int, nu: int, radius: float) -> None:
        self.subdivisions: int = subdivisions
        self.nu: int = nu
        self.radius: float = radius

        self._vertex_map: dict[tuple[float, float, float], int] = {}
        self._raw_vertices: list[np.ndarray] = []
        self._raw_faces: list[list[int]] = []

        self._generate_frequency_icosphere()

    def _add_vertex(self, vertex_coordinates: np.ndarray) -> int:
        normalized_vertex = vertex_coordinates / np.linalg.norm(vertex_coordinates)
        key = tuple(np.round(normalized_vertex, 6))

        if key not in self._vertex_map:
            self._vertex_map[key] = len(self._raw_vertices)
            self._raw_vertices.append(normalized_vertex * self.radius)

        return self._vertex_map[key]

    @staticmethod
    def _get_base_icosahedron() -> tuple[np.ndarray, np.ndarray]:
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

    def _subdivide_face_grid(self, face: np.ndarray, base_vertices: np.ndarray) -> dict[tuple[int, int], int]:
        a = base_vertices[face[0]]
        b = base_vertices[face[1]]
        c = base_vertices[face[2]]

        nu = self.nu
        grid: dict[tuple[int, int], int] = {}
        for i in range(nu + 1):
            for j in range(nu + 1 - i):
                k: int = nu - i - j
                vertex_coordinates: np.ndarray = ((i * a) + (j * b) + (k * c)) / nu
                grid[(i, j)] = self._add_vertex(vertex_coordinates=vertex_coordinates)
        return grid

    def _stitch_face_triangles(self, grid: dict[tuple[int, int], int]) -> None:
        nu = self.nu
        for i in range(nu):
            for j in range(nu - i):
                self._raw_faces.append([grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]])

                if j < nu - i - 1:
                    self._raw_faces.append([grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]])

    def _build_adjacency(self) -> list[list[int]]:
        num_vertices = len(self.vertices)
        neighbors: list[set[int]] = [set() for _ in range(num_vertices)]

        for face in self.faces:
            v0, v1, v2 = int(face[0]), int(face[1]), int(face[2])
            neighbors[v0].add(v1)
            neighbors[v0].add(v2)
            neighbors[v1].add(v0)
            neighbors[v1].add(v2)
            neighbors[v2].add(v0)
            neighbors[v2].add(v1)

        return [sorted(nbr_set) for nbr_set in neighbors]

    def _build_face_centroids(self) -> np.ndarray:
        """Centroid of every triangle face, shape ``(n_faces, 3)``."""
        return self.vertices[self.faces].mean(axis=1)

    def _build_vertex_faces(self) -> list[list[int]]:
        """For each vertex, the face indices that contain it."""
        n_vertices = len(self.vertices)
        vertex_faces: list[list[int]] = [[] for _ in range(n_vertices)]

        for face_idx, face in enumerate(self.faces):
            for v in face:
                vertex_faces[int(v)].append(face_idx)

        return vertex_faces

    def _sort_vertex_faces(self, vertex_idx: int, face_indices: list[int]) -> list[int]:
        """Sort face indices by the angular order of their centroids around a vertex."""
        pos = self.vertices[vertex_idx]
        centroids = self.dual_vertices[face_indices]
        vecs = centroids - pos

        # Use the first centroid as the reference direction.
        ref = vecs[0] / np.linalg.norm(vecs[0])

        # Build a tangent basis from the reference.
        tangent_u = ref
        tangent_v = np.cross(pos, tangent_u)
        tangent_v = tangent_v / np.linalg.norm(tangent_v)
        tangent_u = np.cross(tangent_v, pos)

        # Project onto the tangent plane and sort by angle.
        u = np.dot(vecs, tangent_u)
        v = np.dot(vecs, tangent_v)
        order = np.argsort(np.arctan2(v, u))

        return [face_indices[i] for i in order]

    def _build_dual_mesh(self) -> None:
        """Build dual mesh: hexagons and pentagons from the triangular icosphere."""
        self.dual_vertices = self._build_face_centroids()
        vertex_faces = self._build_vertex_faces()

        self.dual_faces = []
        for v in range(len(self.vertices)):
            sorted_indices = self._sort_vertex_faces(v, vertex_faces[v])
            self.dual_faces.append(sorted_indices)

    def _generate_frequency_icosphere(self) -> None:
        base_vertices, base_faces = self._get_base_icosahedron()

        for face in base_faces:
            grid = self._subdivide_face_grid(face, base_vertices)
            self._stitch_face_triangles(grid)

        self.vertices = np.array(self._raw_vertices)
        self.faces = np.array(self._raw_faces)
        self.neighbors = self._build_adjacency()
        self._build_dual_mesh()

        # Free intermediate build state.
        self._vertex_map = {}
        self._raw_vertices = []
        self._raw_faces = []


