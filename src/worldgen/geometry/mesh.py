import math
import random
from dataclasses import dataclass

import numpy as np
from scipy.spatial import Delaunay, Voronoi

from src.worldgen.geometry.torus import torus_delta_batch
from src.worldgen.types import BoolArray, Float64Array, Int32Array


@dataclass(frozen=True)
class MeshGeometry:
    """Torus mesh layout: site positions and CSR adjacency"""

    width: float
    height: float
    sites: Float64Array
    neighbor_indices: Int32Array
    neighbor_offsets: Int32Array
    # Per-directed-edge geometry, parallel to ``neighbor_indices`` (entry k
    # describes the edge from its source cell to ``neighbor_indices[k]``).
    edge_normals: Float64Array  # (n_edges, 2) unit site->neighbor offset (face outward normal)
    edge_lengths: Float64Array  # (n_edges,) shared Voronoi face length (finite-volume flux weight)

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

    edge_geometry: tuple[Float64Array, Float64Array] = _build_edge_geometry(
        sites=sites,
        site_array=site_array,
        neighbor_indices=indices,
        neighbor_offsets=offsets,
        width=width,
        height=height,
    )

    return MeshGeometry(
        width=width,
        height=height,
        sites=site_array,
        neighbor_indices=indices,
        neighbor_offsets=offsets,
        edge_normals=edge_geometry[0],
        edge_lengths=edge_geometry[1],
    )


def _build_edge_geometry(
    sites: list[tuple[float, float]],
    site_array: Float64Array,
    neighbor_indices: Int32Array,
    neighbor_offsets: Int32Array,
    width: float,
    height: float,
) -> tuple[Float64Array, Float64Array]:
    """Per-directed-edge outward unit normal and shared Voronoi face length.

    Both arrays are parallel to ``neighbor_indices``: entry ``k`` describes the
    edge from its source cell to ``neighbor_indices[k]``. The normal is the unit
    site->neighbor offset on the torus — a Voronoi face is the perpendicular
    bisector of its two sites, so this is the face's outward normal for the
    source cell. The length is the shared Voronoi ridge segment, used to weight
    finite-volume flux across the face.

    Args:
        sites: Canonical site positions as ``(x, y)`` tuples.
        site_array: The same sites as an ``(n, 2)`` float array.
        neighbor_indices: CSR neighbor ids (the directed edges).
        neighbor_offsets: CSR row offsets, length ``n + 1``.
        width: Torus width.
        height: Torus height.

    Returns:
        ``(edge_normals, edge_lengths)``: an ``(n_edges, 2)`` unit-normal array
        and an ``(n_edges,)`` face-length array, both parallel to
        ``neighbor_indices``.
    """
    n: int = int(neighbor_offsets.shape[0]) - 1
    n_edges: int = int(neighbor_indices.shape[0])

    # --- outward normals: unit minimum-image offset from source to neighbor ---
    source: Int32Array = np.repeat(
        np.arange(n, dtype=np.int32), np.diff(neighbor_offsets)
    )
    delta: Float64Array = torus_delta_batch(
        a=site_array[source], b=site_array[neighbor_indices], width=width, height=height
    )
    dist: Float64Array = np.hypot(delta[:, 0], delta[:, 1])
    safe: BoolArray = dist > 0.0
    normals: Float64Array = np.zeros(shape=(n_edges, 2), dtype=np.float64)
    normals[safe] = delta[safe] / dist[safe, None]

    # --- face lengths: shared Voronoi ridge between each adjacent site pair ---
    tile: tuple[list[tuple[float, float]], list[int]] = _tile_sites(
        sites=sites, width=width, height=height
    )
    tiled_to_canonical: list[int] = tile[1]
    voronoi: Voronoi = Voronoi(points=tile[0])
    ridge_points: Int32Array = voronoi.ridge_points
    ridge_vertices: list[list[int]] = voronoi.ridge_vertices

    ridge_length: dict[tuple[int, int], float] = {}
    ridge_id: int
    for ridge_id in range(len(ridge_vertices)):
        vertex_a: int = int(ridge_vertices[ridge_id][0])
        vertex_b: int = int(ridge_vertices[ridge_id][1])
        if vertex_a < 0 or vertex_b < 0:
            continue  # infinite ridge — only on the outer tile copies
        tiled_p: int = int(ridge_points[ridge_id][0])
        tiled_q: int = int(ridge_points[ridge_id][1])
        if tiled_p % 9 != 4 and tiled_q % 9 != 4:
            continue  # neither endpoint is a canonical (center) copy
        canonical_p: int = tiled_to_canonical[tiled_p]
        canonical_q: int = tiled_to_canonical[tiled_q]
        if canonical_p == canonical_q:
            continue
        length: float = float(
            np.hypot(
                voronoi.vertices[vertex_a][0] - voronoi.vertices[vertex_b][0],
                voronoi.vertices[vertex_a][1] - voronoi.vertices[vertex_b][1],
            )
        )
        key: tuple[int, int] = (
            min(canonical_p, canonical_q),
            max(canonical_p, canonical_q),
        )
        ridge_length[key] = length

    lengths: Float64Array = np.full(shape=n_edges, fill_value=np.nan, dtype=np.float64)
    edge_id: int
    for edge_id in range(n_edges):
        source_cell: int = int(source[edge_id])
        target_cell: int = int(neighbor_indices[edge_id])
        lookup: tuple[int, int] = (
            min(source_cell, target_cell),
            max(source_cell, target_cell),
        )
        found: float | None = ridge_length.get(lookup)
        if found is not None:
            lengths[edge_id] = found

    # Cocircular or degenerate faces leave no finite ridge; fall back to the
    # median face length so flux weighting stays positive and well-defined.
    missing: BoolArray = np.isnan(lengths)
    if missing.any():
        fallback: float = float(np.nanmedian(lengths)) if not missing.all() else 1.0
        lengths[missing] = fallback

    return normals, lengths


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
