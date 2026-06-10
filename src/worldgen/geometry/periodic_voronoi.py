from __future__ import annotations

import math
import random

from scipy.spatial import Delaunay, Voronoi

from src.worldgen.model import MeshCell, VoronoiMesh


class PeriodicVoronoi:
    def __init__(self, width: float, height: float) -> None:
        self._width = width
        self._height = height

    def build(
        self,
        seed: int,
        cell_count: int,
        lloyd_iterations: int,
    ) -> VoronoiMesh:
        rng = random.Random(seed)
        sites = self._generate_jittered_sites(cell_count, rng)

        for _ in range(lloyd_iterations):
            sites = self._lloyd_relax(sites)

        neighbor_sets = self._build_neighbor_graph(sites)
        cells = [
            MeshCell(
                id=index,
                site=sites[index],
                neighbors=sorted(neighbor_sets[index]),
            )
            for index in range(len(sites))
        ]
        return VoronoiMesh(width=self._width, height=self._height, cells=cells)

    def _tile_sites(
        self,
        sites: list[tuple[float, float]],
    ) -> tuple[list[tuple[float, float]], list[int]]:
        tiled_points: list[tuple[float, float]] = []
        tiled_to_canonical: list[int] = []
        for index, (x, y) in enumerate(sites):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    tiled_points.append((x + dx * self._width, y + dy * self._height))
                    tiled_to_canonical.append(index)
        return tiled_points, tiled_to_canonical

    def _build_neighbor_graph(
        self,
        sites: list[tuple[float, float]],
    ) -> list[set[int]]:
        tiled_points, tiled_to_canonical = self._tile_sites(sites)
        delaunay = Delaunay(tiled_points)
        neighbors: list[set[int]] = [set() for _ in sites]

        for simplex in delaunay.simplices:
            for i in range(len(simplex)):
                vertex_a = simplex[i]
                vertex_b = simplex[(i + 1) % len(simplex)]
                if vertex_a % 9 != 4 and vertex_b % 9 != 4:
                    continue
                canonical_a = tiled_to_canonical[vertex_a]
                canonical_b = tiled_to_canonical[vertex_b]
                if canonical_a == canonical_b:
                    continue
                neighbors[canonical_a].add(canonical_b)
                neighbors[canonical_b].add(canonical_a)

        return neighbors

    def _generate_jittered_sites(
        self,
        count: int,
        rng: random.Random,
    ) -> list[tuple[float, float]]:
        aspect = self._width / self._height
        cols = max(1, int(math.sqrt(count * aspect)))
        rows = max(1, (count + cols - 1) // cols)
        sites: list[tuple[float, float]] = []

        for row in range(rows):
            for col in range(cols):
                if len(sites) >= count:
                    break
                x = (col + rng.random()) / cols * self._width
                y = (row + rng.random()) / rows * self._height
                sites.append((x % self._width, y % self._height))

        while len(sites) < count:
            sites.append((rng.random() * self._width, rng.random() * self._height))

        return sites[:count]

    def _lloyd_relax(
        self,
        sites: list[tuple[float, float]],
    ) -> list[tuple[float, float]]:
        tiled_points, _ = self._tile_sites(sites)
        voronoi = Voronoi(tiled_points)
        relaxed: list[tuple[float, float]] = []

        for index in range(len(sites)):
            center_vertex = index * 9 + 4
            region_index = voronoi.point_region[center_vertex]
            region = voronoi.regions[region_index]
            if not region or -1 in region:
                relaxed.append(sites[index])
                continue

            vertices = voronoi.vertices[region]
            centroid_x = float(vertices[:, 0].mean())
            centroid_y = float(vertices[:, 1].mean())
            relaxed.append((centroid_x % self._width, centroid_y % self._height))

        return relaxed
