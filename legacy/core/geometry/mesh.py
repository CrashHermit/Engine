import numpy as np
import numba
from numba import types
from numba.typed import Dict, List

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

# -------------------------------------------------------------------------
# Define Numba types globally so they are evaluated by standard Python 
# (The JIT compiler requires type objects to be pre-existing constants)
# -------------------------------------------------------------------------
FLOAT3_TYPE = types.UniTuple(types.float64, 3)
INT2_TYPE = types.UniTuple(types.int64, 2)
FLOAT_1D_ARRAY = types.float64[:]


@numba.njit(cache=True)
def generate_icosphere(nu: int) -> tuple[np.ndarray, np.ndarray]:
    """Subdivide a regular icosahedron into a geodesic sphere.

    Args:
        nu: Subdivision frequency.  Produces ``20 * nu^2`` faces.

    Returns:
        (vertices, faces) as numpy arrays.  Vertices are unit-length.
    """
    vertex_map = Dict.empty(
        key_type=FLOAT3_TYPE,
        value_type=types.int64,
    )

    raw_vertices = List.empty_list(item_type=FLOAT_1D_ARRAY)  # type: ignore
    raw_faces_flat = List.empty_list(item_type=types.int64)  # type: ignore

    inv_nu = 1.0 / float(nu)
    n_faces_base = BASE_FACES.shape[0]

    for face_idx in range(n_faces_base):
        face = BASE_FACES[face_idx]
        va0, va1, va2 = BASE_VERTICES[face[0]]
        vb0, vb1, vb2 = BASE_VERTICES[face[1]]
        vc0, vc1, vc2 = BASE_VERTICES[face[2]]

        grid = Dict.empty(
            key_type=INT2_TYPE,
            value_type=types.int64,
        )

        # ---- grid-point generation ----
        for i in range(nu + 1):
            fi = float(i)
            for j in range(nu + 1 - i):
                fj = float(j)
                fk = float(nu - i - j)

                rx = (fi * va0 + fj * vb0 + fk * vc0) * inv_nu
                ry = (fi * va1 + fj * vb1 + fk * vc1) * inv_nu
                rz = (fi * va2 + fj * vb2 + fk * vc2) * inv_nu

                norm = np.sqrt(rx * rx + ry * ry + rz * rz)
                inv_norm = 1.0 / norm

                rounded = (
                    round(rx * inv_norm, 6),
                    round(ry * inv_norm, 6),
                    round(rz * inv_norm, 6),
                )

                if rounded not in vertex_map:
                    vertex_map[rounded] = len(raw_vertices)
                    raw_vertices.append(np.array([rx, ry, rz], dtype=np.float64))

                grid[(i, j)] = vertex_map[rounded]

        # ---- triangle construction (2 per quad cell) ----
        for i in range(nu):
            for j in range(nu - i):
                a = grid[(i, j)]
                b = grid[(i + 1, j)]
                c = grid[(i, j + 1)]
                raw_faces_flat.append(a)
                raw_faces_flat.append(b)
                raw_faces_flat.append(c)

                if j < nu - i - 1:
                    d = grid[(i + 1, j)]
                    e = grid[(i + 1, j + 1)]
                    f = grid[(i, j + 1)]
                    raw_faces_flat.append(d)
                    raw_faces_flat.append(e)
                    raw_faces_flat.append(f)

    # ---- convert typed lists → numpy arrays ----
    nv = len(raw_vertices)
    vertices = np.zeros((nv, 3), dtype=np.float64)
    for idx in range(nv):
        v = raw_vertices[idx]
        # v is pre-normalized because of logic above, but we enforce it just in case
        n = np.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        inv = 1.0 / n
        vertices[idx, 0] = v[0] * inv
        vertices[idx, 1] = v[1] * inv
        vertices[idx, 2] = v[2] * inv

    nf = len(raw_faces_flat) // 3
    faces = np.zeros((nf, 3), dtype=np.int64)
    for idx in range(nf):
        base = idx * 3
        faces[idx, 0] = raw_faces_flat[base]
        faces[idx, 1] = raw_faces_flat[base + 1]
        faces[idx, 2] = raw_faces_flat[base + 2]

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

            neighbors_list: list[list[int]] = [
                sorted(neighbor_set) for neighbor_set in neighbor_sets
            ]

            self._neighbors = neighbors_list

        assert self._neighbors is not None
        return self._neighbors

    @property
    def dual_vertices(self) -> np.ndarray:
        if self._dual_vertices is None:
            centroids: np.ndarray = self.vertices[self.faces].mean(axis=1)

            norms: np.ndarray = np.linalg.norm(centroids, axis=1, keepdims=True)
            self._dual_vertices = centroids / norms

        assert self._dual_vertices is not None
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

            dual_faces_list: list[list[int]] = []
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
                angular_order: np.ndarray = np.argsort(
                    np.arctan2(tangent_v_component, tangent_u_component)
                )

                dual_faces_list.append([face_indices[i] for i in angular_order])

            self._dual_faces = dual_faces_list

        assert self._dual_faces is not None
        return self._dual_faces
