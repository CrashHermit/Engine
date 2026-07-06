import numpy as np

PHI: float = (1.0 + np.sqrt(5.0)) / 2.0

BASE_VERTICES: np.ndarray = np.array(
    [
        [-1, PHI, 0],
        [1, PHI, 0],
        [-1, -PHI, 0],
        [1, -PHI, 0],
        [0, -1, PHI],
        [0, 1, PHI],
        [0, -1, -PHI],
        [0, 1, -PHI],
        [PHI, 0, -1],
        [PHI, 0, 1],
        [-PHI, 0, -1],
        [-PHI, 0, 1],
    ]
)

BASE_FACES: np.ndarray = np.array(
    [
        [0, 5, 1],
        [0, 1, 7],
        [0, 7, 10],
        [0, 10, 11],
        [0, 11, 5],
        [5, 11, 4],
        [11, 10, 2],
        [10, 7, 6],
        [7, 1, 8],
        [3, 4, 2],
        [3, 2, 6],
        [3, 6, 8],
        [3, 8, 9],
        [3, 9, 4],
        [2, 4, 11],
        [6, 2, 10],
        [8, 6, 7],
        [9, 8, 1],
        [1, 9, 5],
        [5, 9, 4],
    ]
)


def generate_icosphere(nu: int) -> tuple[np.ndarray, np.ndarray]:
    vertex_map: dict[tuple[float, float, float], int] = {}
    raw_vertices: list[np.ndarray] = []
    raw_faces: list[list[int]] = []

    for face in BASE_FACES:
        vertex_a: np.ndarray = BASE_VERTICES[face[0]]
        vertex_b: np.ndarray = BASE_VERTICES[face[1]]
        vertex_c: np.ndarray = BASE_VERTICES[face[2]]

        grid: dict[tuple[int, int], int] = {}

        for i in range(nu + 1):
            for j in range(nu + 1 - i):
                barycentric_weight: int = nu - i - j
                raw_position: np.ndarray = ((i * vertex_a) + (j * vertex_b) + (barycentric_weight * vertex_c)) / nu
                normalized_position: np.ndarray = raw_position / np.linalg.norm(raw_position)
                rounded_key: tuple[float, float, float] = tuple(np.round(normalized_position, 6))

                if rounded_key not in vertex_map:
                    vertex_map[rounded_key] = len(raw_vertices)
                    raw_vertices.append(raw_position)

                grid[(i, j)] = vertex_map[rounded_key]

        for i in range(nu):
            for j in range(nu - i):
                raw_faces.append([grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]])
                if j < nu - i - 1:
                    raw_faces.append([grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]])

    vertices: np.ndarray = np.array(raw_vertices)
    vertices /= np.linalg.norm(vertices, axis=1, keepdims=True)
    faces: np.ndarray = np.array(raw_faces)

    return vertices, faces


class Mesh:
    def __init__(self, vertices: np.ndarray, faces: np.ndarray) -> None:
        self.vertices: np.ndarray = vertices
        self.faces: np.ndarray = faces

        self._neighbors: list[list[int]] | None = None
        self._dual_vertices: np.ndarray | None = None
        self._dual_faces: list[list[int]] | None = None

    @property
    def neighbors(self) -> list[list[int]]:
        if self._neighbors is None:
            num_vertices: int = len(self.vertices)
            neighbor_sets: list[set[int]] = [set() for _ in range(num_vertices)]

            for face in self.faces:
                vertex_a: int = int(face[0])
                vertex_b: int = int(face[1])
                vertex_c: int = int(face[2])

                neighbor_sets[vertex_a].add(vertex_b)
                neighbor_sets[vertex_a].add(vertex_c)
                neighbor_sets[vertex_b].add(vertex_a)
                neighbor_sets[vertex_b].add(vertex_c)
                neighbor_sets[vertex_c].add(vertex_a)
                neighbor_sets[vertex_c].add(vertex_b)

            self._neighbors = [sorted(neighbor_set) for neighbor_set in neighbor_sets]

        return self._neighbors

    @property
    def dual_vertices(self) -> np.ndarray:
        if self._dual_vertices is None:
            self._dual_vertices = self.vertices[self.faces].mean(axis=1)
        return self._dual_vertices

    @property
    def dual_faces(self) -> list[list[int]]:
        if self._dual_faces is None:
            centroids: np.ndarray = self.dual_vertices
            num_vertices: int = len(self.vertices)

            vertex_faces: list[list[int]] = [[] for _ in range(num_vertices)]
            for face_index, face in enumerate(self.faces):
                for vertex in face:
                    vertex_faces[int(vertex)].append(face_index)

            dual: list[list[int]] = []
            for vertex_index in range(num_vertices):
                face_indices: list[int] = vertex_faces[vertex_index]
                position: np.ndarray = self.vertices[vertex_index]
                centroid_vectors: np.ndarray = centroids[face_indices] - position

                reference_norm: float = float(np.linalg.norm(centroid_vectors[0]))
                if reference_norm == 0.0:
                    raise ValueError(
                        f"Vertex {vertex_index}: face centroid coincides with vertex position"
                    )
                reference_vector: np.ndarray = centroid_vectors[0] / reference_norm

                tangent_u: np.ndarray = reference_vector
                tangent_v: np.ndarray = np.cross(position, tangent_u)
                tangent_v_norm: float = float(np.linalg.norm(tangent_v))
                if tangent_v_norm == 0.0:
                    raise ValueError(
                        f"Vertex {vertex_index}: position and reference vector are parallel"
                    )
                tangent_v = tangent_v / tangent_v_norm
                tangent_u = np.cross(tangent_v, position)

                tangent_u_component: np.ndarray = np.dot(centroid_vectors, tangent_u)
                tangent_v_component: np.ndarray = np.dot(centroid_vectors, tangent_v)
                angular_order: np.ndarray = np.argsort(np.arctan2(tangent_v_component, tangent_u_component))

                dual.append([face_indices[i] for i in angular_order])

            self._dual_faces = dual
        return self._dual_faces


