"""Shared field operations over the mesh graph.

One home for graph-field primitives that several stages would otherwise each
hand-roll.  Currently: ``diffuse`` (Jacobi neighbour-mean relaxation), the single
implementation behind hillslope diffusion (erosion), coastline de-speckling
(finalize), and biome-region coherence (ecology).
"""

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def diffuse(
    *,
    geometry: MeshGeometry,
    field: Float64Array,
    strength: float,
    passes: int,
    mask: BoolArray | None = None,
) -> Float64Array:
    """Relax a field toward its mesh-neighbour mean (Jacobi Laplacian smoothing).

    Each pass applies ``x += strength * (neighbour_mean - x)`` to every cell,
    computed double-buffered — all updates read the *previous* pass — so the
    result is order-independent and deterministic.  Handles 1-D ``(n,)`` and 2-D
    ``(n, k)`` fields.

    When ``mask`` is given, only masked neighbours contribute to the mean and
    non-masked cells are held at zero after each pass (e.g. land-only biome
    smoothing that must not bleed toward ocean zeros).  When ``mask`` is ``None``
    every cell participates and the field is smoothed in place of its values.

    Args:
        geometry: Torus mesh with CSR adjacency.
        field: Per-cell values, shape ``(n,)`` or ``(n, k)``.
        strength: Blend toward the neighbour mean per pass, in ``[0, 1]``.
        passes: Number of relaxation passes (``<= 0`` returns a copy unchanged).
        mask: Optional bool mask of participating cells.

    Returns:
        The smoothed field as a new array (the input is not mutated).
    """
    g: Float64Array = field.astype(np.float64, copy=True)
    if passes <= 0 or strength <= 0.0:
        return g

    two_d: bool = g.ndim == 2
    work: Float64Array = g if two_d else g.reshape(-1, 1)
    cols: int = work.shape[1]

    n: int = geometry.n_cells
    indices: Int32Array = geometry.neighbor_indices
    src: Int32Array = np.repeat(
        np.arange(n, dtype=np.int32), np.diff(geometry.neighbor_offsets)
    )

    # Degree (number of contributing neighbours per cell) and per-edge weight.
    # Unmasked: every neighbour counts (edge weight 1).  Masked: only masked
    # neighbours count, so the mean ignores ocean/lake rows.
    if mask is None:
        degree: Float64Array = np.diff(geometry.neighbor_offsets).astype(np.float64)
        edge_weight: Float64Array | None = None
    else:
        maskf: Float64Array = mask.astype(np.float64)
        edge_weight = maskf[indices]
        degree = np.bincount(src, weights=edge_weight, minlength=n)
    safe: BoolArray = degree > 0.0

    for _ in range(passes):
        neighbour_mean: Float64Array = np.empty_like(work)
        col: int
        for col in range(cols):
            neighbour_values: Float64Array = work[indices, col]
            if edge_weight is not None:
                neighbour_values = neighbour_values * edge_weight
            nb_sum: Float64Array = np.bincount(
                src, weights=neighbour_values, minlength=n
            )
            # Cells with no contributing neighbour keep their own value (no change).
            neighbour_mean[:, col] = np.divide(
                nb_sum, degree, out=work[:, col].copy(), where=safe
            )
        work = work + strength * (neighbour_mean - work)
        if mask is not None:
            work[~mask] = 0.0

    return work if two_d else work.reshape(-1)
