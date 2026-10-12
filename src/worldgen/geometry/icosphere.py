"""Numba-accelerated geodesic icosphere generation."""

import numpy as np
import numba
from numba import types
from numba.typed import Dict, List

PHI: float = (1.0 + np.sqrt(5.0)) / 2.0

BASE_VERTICES: np.ndarray = np.array(
    [
        (-1, PHI, 0),
        (1, PHI, 0),
        (-1, -PHI, 0),
        (1, -PHI, 0),
        (0, -1, PHI),
        (0, 1, PHI),
        (0, -1, -PHI),
        (0, 1, -PHI),
        (PHI, 0, -1),
        (PHI, 0, 1),
        (-PHI, 0, -1),
        (-PHI, 0, 1),
    ],
    dtype=np.float64,
)
BASE_FACES: np.ndarray = np.array(
    [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    ],
    dtype=np.int64,
)

_FLOAT3 = types.UniTuple(types.float64, 3)
_INT2 = types.UniTuple(types.int64, 2)
_FLOAT_ARRAY = types.float64[:]


@numba.njit(cache=True)
def generate_icosphere(nu: int) -> tuple[np.ndarray, np.ndarray]:
    """Return unit-sphere vertices and triangular faces."""
    vertex_map = Dict.empty(key_type=_FLOAT3, value_type=types.int64)
    raw_vertices = List.empty_list(item_type=_FLOAT_ARRAY)
    raw_faces = List.empty_list(item_type=types.int64)
    inv_nu = 1.0 / float(nu)

    for face_idx in range(BASE_FACES.shape[0]):
        face = BASE_FACES[face_idx]
        va = BASE_VERTICES[face[0]]
        vb = BASE_VERTICES[face[1]]
        vc = BASE_VERTICES[face[2]]
        grid = Dict.empty(key_type=_INT2, value_type=types.int64)

        for i in range(nu + 1):
            for j in range(nu + 1 - i):
                k = nu - i - j
                point = (i * va + j * vb + k * vc) * inv_nu
                norm = np.sqrt(np.dot(point, point))
                normalized = point / norm
                key = (
                    round(normalized[0], 6),
                    round(normalized[1], 6),
                    round(normalized[2], 6),
                )
                if key not in vertex_map:
                    vertex_map[key] = len(raw_vertices)
                    raw_vertices.append(point)
                grid[(i, j)] = vertex_map[key]

        for i in range(nu):
            for j in range(nu - i):
                a = grid[(i, j)]
                b = grid[(i + 1, j)]
                c = grid[(i, j + 1)]
                raw_faces.extend((a, b, c))
                if j < nu - i - 1:
                    d = grid[(i + 1, j)]
                    e = grid[(i + 1, j + 1)]
                    f = grid[(i, j + 1)]
                    raw_faces.extend((d, e, f))

    vertices = np.zeros((len(raw_vertices), 3), dtype=np.float64)
    for index in range(len(raw_vertices)):
        point = raw_vertices[index]
        vertices[index] = point / np.sqrt(np.dot(point, point))

    faces = np.zeros((len(raw_faces) // 3, 3), dtype=np.int64)
    for index in range(len(raw_faces)):
        faces[index // 3, index % 3] = raw_faces[index]
    return vertices, faces
