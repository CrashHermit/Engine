"""The leyline web: Kruskal MST over nexus edges, plus a few loop edges.

Phase 4 step 3.  The minimum spanning tree is the cheapest set of edges
connecting every nexus — organic, no cycles.  Pure trees feel fragile, so we
add back the shortest few non-tree edges to create loops.
"""

from src.worldgen.config.worldgen_config import LeylineConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import Float64Array


def _find(parent: list[int], x: int) -> int:
    """Union-find root of ``x`` with path compression."""
    root: int = x
    while parent[root] != root:
        root = parent[root]
    while parent[x] != root:
        parent[x], x = root, parent[x]
    return root


def _union(parent: list[int], rank: list[int], a: int, b: int) -> bool:
    """Union the sets of ``a`` and ``b``; return True iff they were disjoint."""
    root_a: int = _find(parent, a)
    root_b: int = _find(parent, b)
    if root_a == root_b:
        return False
    if rank[root_a] < rank[root_b]:
        root_a, root_b = root_b, root_a
    parent[root_b] = root_a
    if rank[root_a] == rank[root_b]:
        rank[root_a] += 1
    return True


def build_web(
    *,
    geometry: MeshGeometry,
    nexus_cells: list[int],
    cfg: LeylineConfig,
) -> list[tuple[int, int]]:
    """Kruskal MST over k-nearest nexus edges, plus the shortest loop edges.

    Edges are stored as **index pairs into ``nexus_cells``**, not raw cell ids.

    Args:
        geometry: Torus mesh providing site positions and dimensions.
        nexus_cells: Mesh cell ids of the placed nexuses.
        cfg: Leyline configuration (``edge_k``, ``extra_loops``).

    Returns:
        edges: MST edges followed by the loop edges, each ``(i, j)`` indexing
            into ``nexus_cells`` with ``i < j``.
    """
    k: int = len(nexus_cells)
    if k <= 1:
        return []

    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height

    # --- candidate edges: each nexus to its edge_k nearest fellows ---
    candidates: dict[tuple[int, int], float] = {}
    i: int
    for i in range(k):
        site_i: Float64Array = sites[nexus_cells[i]]
        dists: list[tuple[float, int]] = []
        j: int
        for j in range(k):
            if j == i:
                continue
            d: float = torus_distance(
                a=site_i, b=sites[nexus_cells[j]], width=width, height=height
            )
            dists.append((d, j))
        dists.sort(key=lambda item: (item[0], item[1]))
        for d, j in dists[: cfg.edge_k]:
            lo: int = min(i, j)
            hi: int = max(i, j)
            candidates[(lo, hi)] = d

    # --- sort candidates deterministically: length, then endpoint indices ---
    sorted_edges: list[tuple[float, int, int]] = sorted(
        (length, lo, hi) for (lo, hi), length in candidates.items()
    )

    # --- Kruskal ---
    parent: list[int] = list(range(k))
    rank: list[int] = [0] * k
    mst: list[tuple[int, int]] = []
    rejected: list[tuple[int, int]] = []

    length: float
    lo: int
    hi: int
    for length, lo, hi in sorted_edges:
        if _union(parent, rank, lo, hi):
            mst.append((lo, hi))
        else:
            rejected.append((lo, hi))

    # --- loops: the shortest rejected edges (already in ascending length) ---
    loops: list[tuple[int, int]] = rejected[: cfg.extra_loops]

    return mst + loops
