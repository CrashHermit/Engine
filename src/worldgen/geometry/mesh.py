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
        self._edge_face_indices: tuple[np.ndarray, ...] | None = None
        self._neighbor_edge_indices: np.ndarray | None = None
        self._edge_lengths_percent: np.ndarray | None = None
        self._geographic_adjacency: tuple[tuple[tuple[int, float], ...], ...] | None = (
            None
        )
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

    @property
    def edge_face_indices(self) -> tuple[np.ndarray, ...]:
        """Return sorted primal face indices incident to each mesh edge."""
        if self._edge_face_indices is None:
            incident: dict[tuple[int, int], list[int]] = defaultdict(list)
            for face_index, face in enumerate(self.faces):
                for index in range(3):
                    left = int(face[index])
                    right = int(face[(index + 1) % 3])
                    incident[(min(left, right), max(left, right))].append(face_index)
            result = []
            for left, right in self.edges:
                values = np.asarray(incident[(int(left), int(right))], dtype=np.int64)
                values.sort()
                values.setflags(write=False)
                result.append(values)
            self._edge_face_indices = tuple(result)
        return self._edge_face_indices

    @property
    def neighbor_edge_indices(self) -> np.ndarray:
        """Return edge indices aligned with the CSR neighbor-index array."""
        if self._neighbor_edge_indices is None:
            edge_lookup = {
                (int(left), int(right)): index
                for index, (left, right) in enumerate(self.edges)
            }
            indices = np.empty(len(self.neighbor_indices), dtype=np.int64)
            position = 0
            for vertex in range(len(self.vertices)):
                start = int(self.neighbor_offsets[vertex])
                end = int(self.neighbor_offsets[vertex + 1])
                for neighbor_value in self.neighbor_indices[start:end]:
                    neighbor = int(neighbor_value)
                    indices[position] = edge_lookup[
                        (min(vertex, neighbor), max(vertex, neighbor))
                    ]
                    position += 1
            indices.setflags(write=False)
            self._neighbor_edge_indices = indices
        return self._neighbor_edge_indices

    @property
    def edge_lengths_percent(self) -> np.ndarray:
        """Return spherical edge lengths as percentages of circumference."""
        if self._edge_lengths_percent is None:
            from src.worldgen.geometry.spherical import angular_distances

            left = self.vertices[self.edges[:, 0]]
            right = self.vertices[self.edges[:, 1]]
            lengths = angular_distances(left, right) * (100.0 / (2.0 * np.pi))
            lengths.setflags(write=False)
            self._edge_lengths_percent = lengths
        return self._edge_lengths_percent

    @property
    def geographic_adjacency(
        self,
    ) -> tuple[tuple[tuple[int, float], ...], ...]:
        """Return immutable sorted neighbors weighted by spherical distance."""
        if self._geographic_adjacency is None:
            edge_lengths = self.edge_lengths_percent
            neighbor_edge_indices = self.neighbor_edge_indices
            adjacency = []
            for vertex in range(len(self.vertices)):
                start = int(self.neighbor_offsets[vertex])
                end = int(self.neighbor_offsets[vertex + 1])
                adjacency.append(
                    tuple(
                        (
                            int(neighbor),
                            float(edge_lengths[edge_index]),
                        )
                        for neighbor, edge_index in zip(
                            self.neighbor_indices[start:end],
                            neighbor_edge_indices[start:end],
                        )
                    )
                )
            self._geographic_adjacency = tuple(adjacency)
        return self._geographic_adjacency

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
