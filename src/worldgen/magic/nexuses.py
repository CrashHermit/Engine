"""Nexus extraction: the poles of the mana flow, as ley-potential extrema.

Phase 4 step 5.  Nexuses are not placed — they are *read* from the combined
potential, the magic mirror of detecting lakes from depressions.  A local
maximum is a SOURCE (magic wells up, a headwater); a local minimum is a SINK
(magic drains, a mouth).  Salient extrema are greedy-spaced so the poles are
iconic rather than a scatter of tiny bumps.
"""

import numpy as np

from src.worldgen.config.worldgen_config import MagicConfig
from src.worldgen.features import Nexus, NexusPolarity
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def extract_nexuses(
    *,
    geometry: MeshGeometry,
    combined_potential: Float64Array,
    source_channels: Float64Array,
    cfg: MagicConfig,
) -> tuple[list[Nexus], Int32Array, BoolArray]:
    """Enumerate salient extrema of the potential as nexus poles.

    For every cell, compare its potential to its neighbours: a strict local
    maximum is a SOURCE, a strict local minimum is a SINK.  Prominence (distance
    from the neighbour mean) is max-normalized to a ``charge`` in ``[0, 1]``;
    extrema below ``cfg.nexus_prominence`` are dropped, and the rest are
    greedy-spaced by charge with ``cfg.nexus_min_spacing``.

    Args:
        geometry: Torus mesh with sites and CSR adjacency.
        combined_potential: Per-cell ley potential.
        source_channels: Per-cell channel identity (for each pole's flavor).
        cfg: Magic configuration (prominence threshold, spacing).

    Returns:
        nexuses: List of ``Nexus`` objects (0-based ids).
        nexus_id: Per-cell nexus id (``-1`` = no nexus).
        is_nexus: Boolean array marking nexus cells.
    """
    n: int = geometry.n_cells
    nexus_id: Int32Array = np.full(n, -1, dtype=np.int32)
    is_nexus: BoolArray = np.zeros(n, dtype=bool)

    # --- 1. find strict local extrema and their raw prominence ---
    is_source: BoolArray = np.zeros(n, dtype=bool)
    is_sink: BoolArray = np.zeros(n, dtype=bool)
    prominence: Float64Array = np.zeros(n, dtype=np.float64)

    cell_id: int
    for cell_id in range(n):
        p_cell: float = float(combined_potential[cell_id])
        neighbors: Int32Array = geometry.neighbors_of(cell_id=cell_id)
        if len(neighbors) == 0:
            continue
        neighbor_vals: Float64Array = combined_potential[neighbors]
        nb_max: float = float(neighbor_vals.max())
        nb_min: float = float(neighbor_vals.min())
        nb_mean: float = float(neighbor_vals.mean())
        if p_cell > nb_max:
            is_source[cell_id] = True
            prominence[cell_id] = abs(p_cell - nb_mean)
        elif p_cell < nb_min:
            is_sink[cell_id] = True
            prominence[cell_id] = abs(p_cell - nb_mean)

    # --- 2. normalize prominence to a [0, 1] charge ---
    prom_max: float = float(prominence.max())
    if prom_max <= 0.0:
        return [], nexus_id, is_nexus
    charge: Float64Array = prominence / prom_max

    candidates: Int32Array = np.flatnonzero(
        (is_source | is_sink) & (charge >= cfg.nexus_prominence)
    ).astype(np.int32)
    if candidates.size == 0:
        return [], nexus_id, is_nexus

    # --- 3. greedy spacing by charge (ties broken by cell id) ---
    order: Int32Array = candidates[
        np.argsort(a=-charge[candidates], kind="stable")
    ]
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    min_d: float = cfg.nexus_min_spacing * max(width, height)

    nexuses: list[Nexus] = []
    accepted: list[int] = []
    cell: int
    for cell in order:
        c: int = int(cell)
        if any(
            torus_distance(a=sites[c], b=sites[a], width=width, height=height) < min_d
            for a in accepted
        ):
            continue
        new_id: int = len(nexuses)
        polarity: NexusPolarity = (
            NexusPolarity.SOURCE if is_source[c] else NexusPolarity.SINK
        )
        nexuses.append(
            Nexus(
                id=new_id,
                cell=c,
                polarity=polarity,
                charge=float(charge[c]),
                channels=source_channels[c].astype(np.float64).copy(),
            )
        )
        nexus_id[c] = new_id
        is_nexus[c] = True
        accepted.append(c)

    return nexuses, nexus_id, is_nexus
