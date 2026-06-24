"""Wind-driven transport on the mesh graph — the shared core of advection.

Both moisture (downwind moisture scatter) and ocean currents (upwind SST gather)
move a scalar along the prevailing wind by weighting each directed mesh edge by
how well the neighbour offset aligns with the source cell's wind.  That per-edge
alignment is the one shared primitive here; each consumer then normalizes it for
its own direction of transport (per-source for a scatter, per-receiver for a
gather).
"""

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def aligned_edges(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
    participates: BoolArray | None = None,
) -> tuple[Int32Array, Int32Array, Float64Array]:
    """Directed mesh edges weighted by wind alignment.

    For each cell ``i`` and neighbour ``j`` we keep the edge ``i -> j`` when the
    wind at ``i`` blows toward ``j`` — ``dot(unit_offset(i, j), wind[i]) > 0`` —
    weighting it by that alignment.  Cells with zero wind contribute no edges.

    When ``participates`` is given, only edges with *both* endpoints in the mask
    are emitted (e.g. the ocean-only subgraph for currents).

    Args:
        geometry: Torus mesh with CSR adjacency.
        wind_u: Wind x-component per cell (unit or zero).
        wind_v: Wind y-component per cell.
        participates: Optional bool mask restricting the edge subgraph.

    Returns:
        ``(src, dst, align)`` flat edge arrays in cell-ascending, CSR-neighbour
        order: edge ``k`` runs ``src[k] -> dst[k]`` with weight ``align[k] > 0``.
    """
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = geometry.n_cells

    src: list[int] = []
    dst: list[int] = []
    align: list[float] = []

    for i in range(n):
        if participates is not None and not participates[i]:
            continue
        wi: float = float(wind_u[i])
        wv: float = float(wind_v[i])
        if wi == 0.0 and wv == 0.0:
            continue
        for neighbor_id in geometry.neighbors_of(cell_id=i):
            j: int = int(neighbor_id)
            if participates is not None and not participates[j]:
                continue
            d: Float64Array = torus_delta(
                a=sites[i], b=sites[j], width=width, height=height
            )
            dist: float = float(np.hypot(d[0], d[1]))
            if dist == 0.0:
                continue
            a: float = (float(d[0]) * wi + float(d[1]) * wv) / dist
            if a > 0.0:
                src.append(i)
                dst.append(j)
                align.append(a)

    return (
        np.array(src, dtype=np.int32),
        np.array(dst, dtype=np.int32),
        np.array(align, dtype=np.float64),
    )


def normalize_per_source(
    *,
    src: Int32Array,
    align: Float64Array,
    n: int,
) -> tuple[Int32Array, Float64Array]:
    """Normalize edge weights so each source cell's outgoing edges sum to one.

    Turns alignment weights into a downwind *distribution* (a scatter): each cell
    fans its payload to its downwind neighbours by these shares.

    Returns ``(indptr, weights)``: ``indptr`` is the CSR row-offset array over
    source cells (length ``n + 1``); ``weights`` is parallel to the input edges.
    """
    indptr: Int32Array = np.zeros(n + 1, dtype=np.int32)
    if src.size == 0:
        return indptr, align
    indptr[1:] = np.cumsum(np.bincount(src, minlength=n))
    totals: Float64Array = np.bincount(src, weights=align, minlength=n)
    weights: Float64Array = align / totals[src]
    return indptr, weights


def normalize_per_receiver(
    *,
    dst: Int32Array,
    align: Float64Array,
    n: int,
) -> Float64Array:
    """Normalize edge weights so each receiving cell's incoming edges sum to one.

    Turns alignment weights into an upwind *gather*: each cell takes the weighted
    mean of the cells flowing into it.  Returns weights parallel to the edges.
    """
    if dst.size == 0:
        return align
    totals: Float64Array = np.bincount(dst, weights=align, minlength=n)
    return align / totals[dst]
