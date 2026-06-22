import math
import random
from dataclasses import dataclass

import numpy as np
from scipy.spatial import Delaunay, Voronoi

from src.worldgen.types import Float64Array, Int32Array


@dataclass(frozen=True)
class MeshGeometry:
    """Torus mesh layout: site positions and CSR adjacency"""

    width: float
    height: float
    sites: Float64Array
    neighbor_indices: Int32Array
    neighbor_offsets: Int32Array

    @property
    def n_cells(self) -> int:
        """Number of Voronoi cells in the mesh."""
        return int(self.sites.shape[0])

    def neighbors_of(self, cell_id: int) -> Int32Array:
        """Return neighbor cell ids for one cell as a zero-copy slice."""
        start: int = int(self.neighbor_offsets[cell_id])
        end: int = int(self.neighbor_offsets[cell_id + 1])
        return self.neighbor_indices[start:end]


def csr_from_lists(
    neighbor_lists: list[set[int]] | list[list[int]],
) -> tuple[Int32Array, Int32Array]:
    """Pack per-cell neighbor lists into CSR (indices, offsets) arrays."""
    n: int = len(neighbor_lists)
    counts: Int32Array = np.fromiter(
        (len(neighbors) for neighbors in neighbor_lists),
        dtype=np.int32,
        count=n,
    )
    offsets: Int32Array = np.empty(shape=n + 1, dtype=np.int32)
    offsets[0] = 0
    np.cumsum(a=counts, out=offsets[1:])

    total: int = int(offsets[-1])
    indices: Int32Array = np.empty(shape=total, dtype=np.int32)
    cursor: int = 0
    neighbor_id: int
    neighbors: set[int] | list[int]
    for neighbors in neighbor_lists:
        for neighbor_id in sorted(neighbors):
            indices[cursor] = neighbor_id
            cursor += 1

    return indices, offsets


def build_mesh(
    seed: int,
    cell_count: int,
    lloyd_iterations: int,
    width: float,
    height: float,
) -> MeshGeometry:
    """Build a periodic Voronoi mesh on a width x height torus."""
    rng: random.Random = random.Random(x=seed)
    sites: list[tuple[float, float]] = _generate_jittered_sites(
        count=cell_count,
        width=width,
        height=height,
        rng=rng,
    )

    for _ in range(lloyd_iterations):
        sites: list[tuple[float, float]] = _lloyd_relax(
            sites=sites,
            width=width,
            height=height,
        )

    neighbor_sets: list[set[int]] = _build_neighbor_graph(
        sites=sites,
        width=width,
        height=height,
    )
    csr: tuple[Int32Array, Int32Array] = csr_from_lists(neighbor_lists=neighbor_sets)
    indices: Int32Array = csr[0]
    offsets: Int32Array = csr[1]
    site_array: Float64Array = np.asarray(a=sites, dtype=np.float64)

    return MeshGeometry(
        width=width,
        height=height,
        sites=site_array,
        neighbor_indices=indices,
        neighbor_offsets=offsets,
    )


def _tile_sites(
    sites: list[tuple[float, float]],
    width: float,
    height: float,
) -> tuple[list[tuple[float, float]], list[int]]:
    """Replicate each site on a 3×3 torus tile for periodic Voronoi/Delaunay."""
    tiled_points: list[tuple[float, float]] = []
    tiled_to_canonical: list[int] = []
    index: int
    x: float
    y: float
    dy: int
    dx: int
    for index, (x, y) in enumerate(sites):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                tiled_points.append((x + dx * width, y + dy * height))
                tiled_to_canonical.append(index)
    return tiled_points, tiled_to_canonical


def _build_neighbor_graph(
    sites: list[tuple[float, float]],
    width: float,
    height: float,
) -> list[set[int]]:
    """Build undirected adjacency from Delaunay edges on the tiled torus."""
    tile: tuple[list[tuple[float, float]], list[int]] = _tile_sites(
        sites=sites,
        width=width,
        height=height,
    )
    tiled_points: list[tuple[float, float]] = tile[0]
    tiled_to_canonical: list[int] = tile[1]
    delaunay: Delaunay = Delaunay(points=tiled_points)
    neighbors: list[set[int]] = [set[int]() for _ in sites]

    simplex: Int32Array
    i: int
    vertex_a: int
    vertex_b: int
    canonical_a: int
    canonical_b: int
    for simplex in delaunay.simplices:
        for i in range(len(simplex)):
            vertex_a: int = int(simplex[i])
            vertex_b: int = int(simplex[(i + 1) % len(simplex)])
            if vertex_a % 9 != 4 and vertex_b % 9 != 4:
                continue
            canonical_a: int = tiled_to_canonical[vertex_a]
            canonical_b: int = tiled_to_canonical[vertex_b]
            if canonical_a == canonical_b:
                continue
            neighbors[canonical_a].add(canonical_b)
            neighbors[canonical_b].add(canonical_a)

    return neighbors


def _generate_jittered_sites(
    count: int,
    width: float,
    height: float,
    rng: random.Random,
) -> list[tuple[float, float]]:
    """Place one jittered point per grid cell for even-but-organic site distribution."""
    aspect: float = width / height
    cols: int = max(1, int(math.sqrt(count * aspect)))
    rows: int = max(1, (count + cols - 1) // cols)
    sites: list[tuple[float, float]] = []

    row: int
    col: int
    x: float
    y: float
    for row in range(rows):
        for col in range(cols):
            if len(sites) >= count:
                break
            x: float = (col + rng.random()) / cols * width
            y: float = (row + rng.random()) / rows * height
            sites.append((x % width, y % height))

    while len(sites) < count:
        sites.append((rng.random() * width, rng.random() * height))

    return sites[:count]


def _lloyd_relax(
    sites: list[tuple[float, float]],
    width: float,
    height: float,
) -> list[tuple[float, float]]:
    """Move each site toward its Voronoi cell centroid on the torus."""
    tile: tuple[list[tuple[float, float]], list[int]] = _tile_sites(
        sites=sites,
        width=width,
        height=height,
    )
    tiled_points: list[tuple[float, float]] = tile[0]
    voronoi: Voronoi = Voronoi(points=tiled_points)
    relaxed: list[tuple[float, float]] = []

    index: int
    center_vertex: int
    region_index: int
    region: list[int]
    centroid_x: float
    centroid_y: float
    for index in range(len(sites)):
        center_vertex: int = index * 9 + 4
        region_index: int = int(voronoi.point_region[center_vertex])
        region: list[int] = voronoi.regions[region_index]
        if not region or -1 in region:
            relaxed.append(sites[index])
            continue

        vertices: Float64Array = voronoi.vertices[region]
        centroid_x: float = float(vertices[:, 0].mean())
        centroid_y: float = float(vertices[:, 1].mean())
        relaxed.append((centroid_x % width, centroid_y % height))

    return relaxed
