"""Topology and derived dual geometry for spherical world cells."""

from collections import defaultdict

import numpy as np


class Mesh:
    """Fixed spherical topology shared by all generated fields."""

    def __init__(self, vertices: np.ndarray, faces: np.ndarray) -> None:
        self.vertices = np.asarray(vertices, dtype=np.float64)
        self.faces = np.asarray(faces, dtype=np.int64)
        self.edges = self._build_edges()
        self.neighbor_offsets, self.neighbor_indices = self._build_csr_adjacency()
        self._dual_vertices: np.ndarray | None = None
        self._dual_faces: list[list[int]] | None = None
        for array in (
            self.vertices,
            self.faces,
            self.edges,
            self.neighbor_offsets,
            self.neighbor_indices,
        ):
            array.setflags(write=False)

    def _build_edges(self) -> np.ndarray:
        edges = np.sort(
            np.concatenate(
                (
                    self.faces[:, [0, 1]],
                    self.faces[:, [1, 2]],
                    self.faces[:, [2, 0]],
                ),
                axis=0,
            ),
            axis=1,
        )
        return np.unique(edges, axis=0)

    def _build_csr_adjacency(self) -> tuple[np.ndarray, np.ndarray]:
        neighbors: list[list[int]] = [[] for _ in range(len(self.vertices))]
        for left, right in self.edges:
            left_index = int(left)
            right_index = int(right)
            neighbors[left_index].append(right_index)
            neighbors[right_index].append(left_index)
        offsets = np.zeros(len(neighbors) + 1, dtype=np.int64)
        for index, values in enumerate(neighbors):
            values.sort()
            offsets[index + 1] = offsets[index] + len(values)
        indices = np.asarray(
            [neighbor for values in neighbors for neighbor in values], dtype=np.int64
        )
        return offsets, indices

    def neighbors(self, cell_id: int) -> np.ndarray:
        start = self.neighbor_offsets[cell_id]
        end = self.neighbor_offsets[cell_id + 1]
        return self.neighbor_indices[start:end]

    @property
    def dual_vertices(self) -> np.ndarray:
        if self._dual_vertices is None:
            centroids = self.vertices[self.faces].mean(axis=1)
            self._dual_vertices = centroids / np.linalg.norm(
                centroids, axis=1, keepdims=True
            )
            self._dual_vertices.setflags(write=False)
        return self._dual_vertices

    @property
    def dual_faces(self) -> list[list[int]]:
        if self._dual_faces is None:
            incident: dict[int, list[int]] = defaultdict(list)
            for face_index, face in enumerate(self.faces):
                for vertex in face:
                    incident[int(vertex)].append(face_index)
            dual_faces: list[list[int]] = []
            for vertex_index in range(len(self.vertices)):
                face_indices = incident[vertex_index]
                position = self.vertices[vertex_index]
                vectors = self.dual_vertices[face_indices] - position
                reference = vectors[0] / np.linalg.norm(vectors[0])
                tangent_v = np.cross(position, reference)
                tangent_v /= np.linalg.norm(tangent_v)
                tangent_u = np.cross(tangent_v, position)
                angles = np.arctan2(
                    vectors @ tangent_v,
                    vectors @ tangent_u,
                )
                dual_faces.append([face_indices[index] for index in np.argsort(angles)])
            self._dual_faces = dual_faces
        return self._dual_faces
