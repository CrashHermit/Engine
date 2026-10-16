"""Topology helpers for boundaries drawn on the dual mesh."""

from collections import defaultdict

import numpy as np

from src.worldgen.geometry.mesh import Mesh


def boundary_components(
    mesh: Mesh, edge_indices: np.ndarray, labels: np.ndarray
) -> np.ndarray:
    """Assign connected dual boundary edges with equal labels to components."""
    edge_indices = np.asarray(edge_indices, dtype=np.int64)
    if len(edge_indices) == 0:
        return np.empty(0, dtype=np.int64)
    incidence = mesh.edge_face_indices
    by_face: dict[int, list[int]] = defaultdict(list)
    for selected, edge_value in enumerate(edge_indices):
        for face in incidence[int(edge_value)]:
            by_face[int(face)].append(selected)
    neighbors: list[list[int]] = [[] for _ in edge_indices]
    for selected_values in by_face.values():
        for left_position, left in enumerate(selected_values):
            for right in selected_values[left_position + 1 :]:
                if np.array_equal(labels[left], labels[right]):
                    neighbors[left].append(right)
                    neighbors[right].append(left)
    components = np.full(len(edge_indices), -1, dtype=np.int64)
    component = 0
    for start in range(len(edge_indices)):
        if components[start] != -1:
            continue
        components[start] = component
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in sorted(neighbors[current], reverse=True):
                if components[neighbor] == -1:
                    components[neighbor] = component
                    stack.append(neighbor)
        component += 1
    return components
