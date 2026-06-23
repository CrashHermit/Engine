"""Single source of truth for what happens at every plate boundary.

One walk over the mesh border edges produces, per cell, the dominant convergent
and divergent interactions with a neighboring plate: their magnitudes, the
plate-pair type (oceanic/continental), and, for convergence, which side is the
overriding plate of the subduction.  Both ``boundary_uplift`` (mountain belts,
rift valleys) and the vulcanism stage (arcs, ridges, volcano placement) read
these facts instead of re-deriving the convergence math, so the two never drift
apart.
"""

from dataclasses import dataclass
from enum import IntEnum

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.types import BoolArray, Float64Array, Int8Array, Int32Array


class BoundaryKind(IntEnum):
    """Plate-pair classification of a boundary interaction (O = oceanic, C = continental)."""

    NONE = 0
    CONV_OO = 1  # convergent ocean-ocean: subduction -> island arc
    CONV_OC = 2  # convergent ocean-continent: subduction -> continental arc
    CONV_CC = 3  # convergent continent-continent: collision, no volcanism
    DIV_OO = 4  # divergent ocean-ocean: mid-ocean ridge
    DIV_OC = 5  # divergent ocean-continent: continental rift margin
    DIV_CC = 6  # divergent continent-continent: continental rift valley


@dataclass(frozen=True)
class BoundaryFacts:
    """Per-cell dominant boundary interactions (length ``n_cells`` each).

    Convergent and divergent interactions are tracked separately so a cell that
    borders one converging and one diverging plate keeps both stories.
    """

    convergence: Float64Array  # dominant convergent rate (>= 0; 0 = none)
    conv_kind: Int8Array  # BoundaryKind of that convergence (NONE / CONV_*)
    is_overriding: BoolArray  # at that convergence, cell is on the overriding plate
    divergence: Float64Array  # dominant divergent rate (>= 0; 0 = none)
    div_kind: Int8Array  # BoundaryKind of that divergence (NONE / DIV_*)


def _conv_kind(continental_i: bool, continental_j: bool) -> int:
    """Convergent BoundaryKind for a plate pair."""
    if continental_i and continental_j:
        return int(BoundaryKind.CONV_CC)
    if continental_i or continental_j:
        return int(BoundaryKind.CONV_OC)
    return int(BoundaryKind.CONV_OO)


def _div_kind(continental_i: bool, continental_j: bool) -> int:
    """Divergent BoundaryKind for a plate pair."""
    if continental_i and continental_j:
        return int(BoundaryKind.DIV_CC)
    if continental_i or continental_j:
        return int(BoundaryKind.DIV_OC)
    return int(BoundaryKind.DIV_OO)


def _overrides(plate_i: int, plate_j: int, density: Float64Array) -> bool:
    """True if ``plate_i`` is the overriding (non-subducting) plate.

    The denser plate sinks, so the lighter plate overrides.  Ties — which the
    density jitter is designed to avoid — break by lower plate id for
    determinism.
    """
    di: float = float(density[plate_i])
    dj: float = float(density[plate_j])
    if di == dj:
        return plate_i < plate_j
    return di < dj


def classify_boundaries(
    *,
    geometry: MeshGeometry,
    plate_id: Int32Array,
    properties: PlateProperties,
) -> BoundaryFacts:
    """Walk every plate border once and return per-cell :class:`BoundaryFacts`.

    Convergence is the closing speed ``dot(drift_i - drift_j, direction)`` toward
    a neighbor on another plate (positive = converging, negative = diverging) —
    the same quantity the old boundary-uplift walk computed, now classified by
    plate type and subduction polarity.

    Args:
        geometry: Torus mesh with sites and CSR adjacency.
        plate_id: Per-cell plate id.
        properties: Per-plate drift, continental flags, and density.

    Returns:
        Per-cell boundary facts (see :class:`BoundaryFacts`).
    """
    n: int = geometry.n_cells
    drift: Float64Array = properties.drift
    is_continental: BoolArray = properties.is_continental
    density: Float64Array = properties.density
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height

    convergence: Float64Array = np.zeros(n, dtype=np.float64)
    conv_kind: Int8Array = np.zeros(n, dtype=np.int8)
    is_overriding: BoolArray = np.zeros(n, dtype=bool)
    divergence: Float64Array = np.zeros(n, dtype=np.float64)
    div_kind: Int8Array = np.zeros(n, dtype=np.int8)

    cell_id: int
    for cell_id in range(n):
        plate_i: int = int(plate_id[cell_id])
        drift_i: Float64Array = drift[plate_i]
        continental_i: bool = bool(is_continental[plate_i])
        site_i: Float64Array = sites[cell_id]

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor: int = int(neighbor_id)
            plate_j: int = int(plate_id[neighbor])
            if plate_j == plate_i:
                continue

            delta: Float64Array = torus_delta(
                a=site_i, b=sites[neighbor], width=width, height=height
            )
            dist: float = float(np.linalg.norm(x=delta))
            if dist == 0.0:
                continue
            direction: Float64Array = delta / dist
            closing: float = float(np.dot(a=drift_i - drift[plate_j], b=direction))
            continental_j: bool = bool(is_continental[plate_j])

            if closing > convergence[cell_id]:
                convergence[cell_id] = closing
                conv_kind[cell_id] = _conv_kind(continental_i, continental_j)
                is_overriding[cell_id] = _overrides(plate_i, plate_j, density)
            elif -closing > divergence[cell_id]:
                divergence[cell_id] = -closing
                div_kind[cell_id] = _div_kind(continental_i, continental_j)

    return BoundaryFacts(
        convergence=convergence,
        conv_kind=conv_kind,
        is_overriding=is_overriding,
        divergence=divergence,
        div_kind=div_kind,
    )
