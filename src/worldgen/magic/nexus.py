"""Nexus placement: score + greedy spacing.

Phase 4 step 2.  Nexuses should sit at *significant* places (peaks, lake
mouths, river forks, ring lines) without bunching up.  The standard pattern is
score-every-candidate then greedily accept the best with a minimum spacing.
"""

import numpy as np

from src.worldgen.config.worldgen_config import LeylineConfig
from src.worldgen.features import Lake
from src.worldgen.fields import MeshFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def _river_inflow_count(
    *, receiver: Int32Array, is_river: BoolArray, n: int
) -> Int32Array:
    """Count, per cell, how many river cells flow into it (river confluences).

    Mirrors the Phase 3 step-3 in-river-degree: a contributor is a river cell
    whose ``receiver`` is this cell *and* whose receiver is itself a river cell.
    """
    inflow: Int32Array = np.zeros(n, dtype=np.int32)
    src: Int32Array = np.flatnonzero(is_river & (receiver >= 0)).astype(np.int32)
    if src.size == 0:
        return inflow
    # Keep only contributors whose receiver is also a river cell.
    src = src[is_river[receiver[src]]]
    if src.size == 0:
        return inflow
    counts: Int32Array = np.bincount(receiver[src], minlength=n).astype(np.int32)
    return counts


def place_nexuses(
    *,
    geometry: MeshGeometry,
    fields: MeshFields,
    lakes: list[Lake],
    cfg: LeylineConfig,
    score_noise: Float64Array,
) -> list[int]:
    """Score every land cell, then greedily accept the best with torus-spacing.

    Score = peak bonus + lake-outlet bonus + confluence bonus + ring-alignment
    bonus + score noise.  Candidates are taken in descending score (ties broken
    by cell id) and accepted only if their ``torus_distance`` to every accepted
    nexus is at least ``cfg.min_spacing`` of the world span.

    Args:
        geometry: Torus mesh with sites and dimensions.
        fields: Mesh fields (elevation, is_land, is_river, receiver, insolation).
        lakes: Extracted lakes (their outlet cells score a bonus).
        cfg: Leyline configuration (bonuses, spacing, count).
        score_noise: Per-cell FBm sample in roughly [-1, 1] for score jitter.

    Returns:
        nexus_cells: Accepted nexus cell ids (descending-score order).
    """
    n: int = geometry.n_cells

    elevation: Float64Array = _require(fields.elevation, "elevation")
    is_land: BoolArray = _require(fields.is_land, "is_land")
    is_river: BoolArray = _require(fields.is_river, "is_river")
    receiver: Int32Array = _require(fields.receiver, "receiver")
    insolation: Float64Array = _require(fields.insolation, "insolation")

    # --- score components (array math) ---
    score: Float64Array = np.zeros(n, dtype=np.float64)

    # Peaks: top elevation percentile among land cells.
    if np.any(is_land):
        peak_z: float = float(
            np.percentile(a=elevation[is_land], q=cfg.peak_percentile)
        )
        is_peak: BoolArray = is_land & (elevation >= peak_z)
        score += cfg.peak_bonus * is_peak.astype(np.float64)

    # Lake outlets: spill cells where water leaves a lake.
    for lake in lakes:
        if lake.outlet_cell is not None:
            score[lake.outlet_cell] += cfg.lake_outlet_bonus

    # Confluences: river cells with >= 2 river inflows.
    inflow: Int32Array = _river_inflow_count(receiver=receiver, is_river=is_river, n=n)
    is_confluence: BoolArray = is_river & (inflow >= 2)
    score += cfg.confluence_bonus * is_confluence.astype(np.float64)

    # Volcanism: live volcanic ground (arcs, ridges, hotspots) draws leylines.
    volcanism: Float64Array | None = fields.volcanism
    if volcanism is not None:
        score += cfg.volcano_bonus * volcanism

    # Ring alignment: cells near the hot/cold ring lines (insolation extremes).
    ring: Float64Array = np.abs(2.0 * insolation - 1.0)
    score += cfg.ring_bonus * ring

    # Noise jitter mapped to [0, 1].
    score += cfg.score_noise * (score_noise + 1.0) * 0.5

    # Ocean cells are never nexuses.
    score = np.where(is_land, score, -np.inf)

    # --- greedy spacing ---
    # Descending score; np.argsort is ascending and stable, so negating and
    # sorting keeps cell-id order within ties → deterministic.
    order: Int32Array = np.argsort(a=-score, kind="stable").astype(np.int32)

    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    min_dist: float = cfg.min_spacing * max(width, height)

    accepted: list[int] = []
    cell_id: int
    for cell_id in order:
        cell: int = int(cell_id)
        if not np.isfinite(score[cell]):
            break  # reached the ocean cells (-inf) — nothing left to place
        site_c: Float64Array = sites[cell]
        too_close: bool = any(
            torus_distance(a=site_c, b=sites[acc], width=width, height=height)
            < min_dist
            for acc in accepted
        )
        if too_close:
            continue
        accepted.append(cell)
        if len(accepted) >= cfg.count:
            break

    return accepted


def _require(value, name: str):
    """Narrow an optional mesh field to non-None or raise."""
    if value is None:
        msg: str = f"{name} must be set before nexus placement"
        raise RuntimeError(msg)
    return value
