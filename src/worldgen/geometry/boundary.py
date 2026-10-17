"""Exact ownership and indexed distance queries for spherical dual boundaries."""

import numpy as np
from scipy.spatial import cKDTree

from src.worldgen.geometry.mesh import Mesh


_PERCENT_PER_RADIAN = 100.0 / (2.0 * np.pi)


def _unit(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    return points / np.linalg.norm(points, axis=-1, keepdims=True)


def _chord(angle: float | np.ndarray) -> float | np.ndarray:
    return 2.0 * np.sin(np.asarray(angle) * 0.5)


def arc_distances(
    points: np.ndarray, starts: np.ndarray, ends: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return exact minor-arc distances in percent circumference and closest points.

    Inputs broadcast over all leading dimensions and have a final dimension of 3.
    """
    points, starts, ends = np.broadcast_arrays(
        _unit(points), _unit(starts), _unit(ends)
    )
    cross = np.cross(starts, ends)
    normal_length = np.linalg.norm(cross, axis=-1, keepdims=True)
    normal = cross / np.maximum(normal_length, np.finfo(np.float64).tiny)
    projected = points - np.sum(points * normal, axis=-1, keepdims=True) * normal
    projected_length = np.linalg.norm(projected, axis=-1, keepdims=True)
    projected /= np.maximum(projected_length, np.finfo(np.float64).tiny)
    # Select the antipode lying on the minor arc, then test whether the projection
    # lies between its endpoints using the sum of sub-arc angles.
    projection = np.where(
        np.sum(projected * points, axis=-1, keepdims=True) >= 0.0, projected, -projected
    )
    arc_angle = np.arctan2(normal_length[..., 0], np.sum(starts * ends, axis=-1))
    first_angle = np.arctan2(
        np.linalg.norm(np.cross(starts, projection), axis=-1),
        np.sum(starts * projection, axis=-1),
    )
    second_angle = np.arctan2(
        np.linalg.norm(np.cross(projection, ends), axis=-1),
        np.sum(projection * ends, axis=-1),
    )
    on_arc = (first_angle + second_angle <= arc_angle + 2e-12) & (
        projected_length[..., 0] > np.finfo(np.float64).eps
    )
    closest = np.where(
        on_arc[..., None],
        projection,
        np.where((first_angle <= second_angle)[..., None], starts, ends),
    )
    angle = np.arctan2(
        np.linalg.norm(np.cross(points, closest), axis=-1),
        np.sum(points * closest, axis=-1),
    )
    return angle * _PERCENT_PER_RADIAN, closest


class SphericalRegions:
    """Indexed exact point ownership by the mesh's centroid-dual polygons."""

    def __init__(self, mesh: Mesh) -> None:
        self.mesh = mesh
        self._faces = tuple(
            np.asarray(face, dtype=np.int64) for face in mesh.dual_faces
        )
        self._centers = mesh.vertices
        self._corners = mesh.dual_vertices
        # Every polygon lies in the cap around its primal vertex reaching its
        # farthest dual corner. This gives a conservative candidate query.
        radii = np.array(
            [
                np.max(
                    np.arctan2(
                        np.linalg.norm(
                            np.cross(mesh.vertices[i], self._corners[face]), axis=1
                        ),
                        self._corners[face] @ mesh.vertices[i],
                    )
                )
                for i, face in enumerate(self._faces)
            ]
        )
        self._max_radius = float(radii.max(initial=0.0))
        self._tree = cKDTree(self._centers)
        self._edge_normals: list[np.ndarray] = []
        self._edge_signs: list[np.ndarray] = []
        for i, face in enumerate(self._faces):
            vertices = self._corners[face]
            normals = np.cross(vertices, np.roll(vertices, -1, axis=0))
            normals /= np.linalg.norm(normals, axis=1, keepdims=True)
            signs = np.sign(normals @ mesh.vertices[i])
            self._edge_normals.append(normals)
            self._edge_signs.append(signs)

    def locate(self, points: np.ndarray) -> np.ndarray:
        points = _unit(np.asarray(points, dtype=np.float64))
        original_shape = points.shape[:-1]
        flat = points.reshape((-1, 3))
        if len(flat) == 0:
            return np.empty(original_shape, dtype=np.int64)
        candidates = self._tree.query_ball_point(flat, _chord(self._max_radius) + 1e-12)
        result = np.empty(len(flat), dtype=np.int64)
        for pindex, (point, cells) in enumerate(zip(flat, candidates, strict=True)):
            matches = []
            for cell in cells:
                inside = (
                    self._edge_signs[cell] * (self._edge_normals[cell] @ point)
                    >= -2e-12
                )
                if np.all(inside):
                    matches.append(cell)
            result[pindex] = min(matches)
        return result.reshape(original_shape)


class BoundaryNetwork:
    """Indexed dual arcs separating labels on the primal mesh."""

    def __init__(
        self, mesh: Mesh, labels: np.ndarray, edge_indices: np.ndarray | None = None
    ) -> None:
        self.mesh = mesh
        labels = np.asarray(labels)
        if edge_indices is None:
            selected = np.flatnonzero(
                labels[mesh.edges[:, 0]] != labels[mesh.edges[:, 1]]
            )
        else:
            selected = np.asarray(edge_indices, dtype=np.int64)
        self.edge_indices = selected.copy()
        self.left_labels = labels[mesh.edges[selected, 0]].copy()
        self.right_labels = labels[mesh.edges[selected, 1]].copy()
        incidence = mesh.edge_face_indices
        self.vertex_indices = np.asarray(
            [incidence[int(edge)] for edge in selected], dtype=np.int64
        ).reshape((-1, 2))
        self.starts = mesh.dual_vertices[self.vertex_indices[:, 0]].copy()
        self.ends = mesh.dual_vertices[self.vertex_indices[:, 1]].copy()
        for array in (
            self.edge_indices,
            self.left_labels,
            self.right_labels,
            self.vertex_indices,
            self.starts,
            self.ends,
        ):
            array.setflags(write=False)
        self._midpoints = (
            _unit(self.starts + self.ends) if len(selected) else self.starts.copy()
        )
        self._half_lengths = (
            np.arctan2(
                np.linalg.norm(np.cross(self.starts, self.ends), axis=1),
                np.sum(self.starts * self.ends, axis=1),
            )
            * 0.5
        )
        self._max_half_length = float(self._half_lengths.max(initial=0.0))
        self._tree = cKDTree(self._midpoints) if len(selected) else None

    def _point_candidates(self, points: np.ndarray) -> list[list[int]]:
        if self._tree is None:
            return [[] for _ in points]
        nearest_distance, nearest_id = self._tree.query(points, k=1)
        midpoint_angle = 2.0 * np.arcsin(np.clip(nearest_distance * 0.5, 0.0, 1.0))
        upper = midpoint_angle + self._half_lengths[nearest_id]
        radii = np.minimum(np.pi, upper + self._max_half_length)
        return [
            np.sort(ids).tolist()
            for ids in self._tree.query_ball_point(points, _chord(radii) + 1e-12)
        ]

    def nearest(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return nearest finite-arc distance, segment ID, and closest point."""
        points = _unit(np.asarray(points, dtype=np.float64))
        shape = points.shape[:-1]
        flat = points.reshape((-1, 3))
        if self._tree is None:
            return (
                np.full(shape, np.inf),
                np.full(shape, -1, dtype=np.int64),
                np.zeros(shape + (3,), dtype=np.float64),
            )
        if len(flat) == 0:
            return (
                np.empty(shape),
                np.empty(shape, dtype=np.int64),
                np.empty(shape + (3,), dtype=np.float64),
            )
        distances = np.full(len(flat), np.inf, dtype=np.float64)
        indices = np.full(len(flat), len(self.starts), dtype=np.int64)
        closest = np.zeros((len(flat), 3), dtype=np.float64)
        candidate_sets = self._point_candidates(flat)
        chunk_size = 65_536
        point_chunks: list[np.ndarray] = []
        segment_chunks: list[np.ndarray] = []
        chunk_count = 0

        def evaluate_chunk() -> None:
            nonlocal chunk_count
            point_ids = np.concatenate(point_chunks)
            segment_ids = np.concatenate(segment_chunks)
            candidate_distances, candidate_points = arc_distances(
                flat[point_ids], self.starts[segment_ids], self.ends[segment_ids]
            )
            order = np.lexsort((segment_ids, candidate_distances, point_ids))
            ordered_points = point_ids[order]
            first = np.r_[True, ordered_points[1:] != ordered_points[:-1]]
            winners = order[first]
            winner_points = point_ids[winners]
            winner_segments = segment_ids[winners]
            winner_distances = candidate_distances[winners]
            improve = (winner_distances < distances[winner_points]) | (
                (winner_distances == distances[winner_points])
                & (winner_segments < indices[winner_points])
            )
            winner_points = winner_points[improve]
            winners = winners[improve]
            distances[winner_points] = candidate_distances[winners]
            indices[winner_points] = segment_ids[winners]
            closest[winner_points] = candidate_points[winners]
            point_chunks.clear()
            segment_chunks.clear()
            chunk_count = 0

        for point_id, candidate_ids in enumerate(candidate_sets):
            ids = np.asarray(candidate_ids, dtype=np.int64)
            offset = 0
            while offset < len(ids):
                take = min(chunk_size - chunk_count, len(ids) - offset)
                segment_chunks.append(ids[offset : offset + take])
                point_chunks.append(np.full(take, point_id, dtype=np.int64))
                chunk_count += take
                offset += take
                if chunk_count == chunk_size:
                    evaluate_chunk()
        if chunk_count:
            evaluate_chunk()
        return (
            distances.reshape(shape),
            indices.reshape(shape),
            closest.reshape(shape + (3,)),
        )

    def candidates(self, points: np.ndarray, radius_percent: float) -> list[np.ndarray]:
        points = _unit(np.asarray(points, dtype=np.float64)).reshape((-1, 3))
        if len(points) == 0 or self._tree is None:
            return [np.empty(0, dtype=np.int64) for _ in points]
        radius = max(0.0, float(radius_percent)) / _PERCENT_PER_RADIAN
        found = self._tree.query_ball_point(
            points, _chord(min(np.pi, radius + self._max_half_length)) + 1e-12
        )
        return [np.asarray(ids, dtype=np.int64) for ids in found]
