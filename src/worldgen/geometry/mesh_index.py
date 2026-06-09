from __future__ import annotations

from scipy.spatial import cKDTree

from src.worldgen.data import VoronoiMesh


class VoronoiMeshIndex:
    def __init__(self, mesh: VoronoiMesh) -> None:
        self._mesh = mesh
        points = [(cell.site[0], cell.site[1]) for cell in mesh.cells]
        self._site_tree = cKDTree(points)

    def nearest_cell_id(self, fx: float, fy: float) -> int:
        mesh = self._mesh
        best_dist = float("inf")
        best_id = 0
        for dx in (-mesh.width, 0.0, mesh.width):
            for dy in (-mesh.height, 0.0, mesh.height):
                dist, index = self._site_tree.query((fx + dx, fy + dy))
                if dist < best_dist:
                    best_dist = dist
                    best_id = int(index)
        return best_id
