"""Vein classification and object extraction (mirror of water/rivers.py).

Step 4: ``classify_veins`` — which cells carry a leyline based on the magic
strength percentile.  Then ``extract_veins`` — labeled downstream-first paths
through the receiver forest over the ley potential, the magic mirror of rivers.
"""

import numpy as np

from src.worldgen.config.worldgen_config import MagicConfig
from src.worldgen.features import Vein
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def classify_veins(
    *,
    magic_strength: Float64Array,
    cfg: MagicConfig,
) -> BoolArray:
    """Classify vein cells by magic-strength percentile.

    ``is_vein = magic_strength >= threshold`` where ``threshold`` is the
    ``cfg.vein_percentile`` quantile of strength — self-adjusting across worlds.
    Magic exists at sea too, so there is no land mask.

    Args:
        magic_strength: Per-cell accumulated mana strength in [0, 1].
        cfg: Magic configuration (``vein_percentile``).

    Returns:
        is_vein: Boolean array marking vein cells.
    """
    threshold: float = float(np.percentile(a=magic_strength, q=cfg.vein_percentile))
    return magic_strength >= threshold


def extract_veins(
    *,
    geometry: MeshGeometry,
    receiver: Int32Array,
    magic_strength: Float64Array,
    channels: Float64Array,
    potential_routed: Float64Array,
    is_vein: BoolArray,
    nexus_id: Int32Array,
) -> tuple[list[Vein], Int32Array]:
    """Build downstream-first Vein objects from the receiver forest.

    Mirror of ``extract_rivers``: process vein cells in descending
    ``potential_routed`` order; at a junction the inflow with the largest
    strength keeps the vein identity, the others record ``tributary_of``.  A vein
    ends (records its ``mouth``) when its receiver is base level (``-1``) or a
    non-vein cell.  Strength ties at junctions break by vein id (lower wins).

    Args:
        geometry: Torus mesh (kept for API parity; only the receiver tree is used).
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        magic_strength: Per-cell accumulated mana strength.
        channels: Per-cell channel composition (n, 3).
        potential_routed: Per-cell routed ley potential (topological order).
        is_vein: Boolean mask identifying vein cells.
        nexus_id: Per-cell nexus id (``-1`` = none), for source/mouth poles.

    Returns:
        veins: List of ``Vein`` objects (0-based ids).
        vein_id: Per-cell vein id (``-1`` = no vein).
    """
    n: int = int(receiver.shape[0])
    vein_cells: Int32Array = np.flatnonzero(is_vein).astype(np.int32)
    if len(vein_cells) == 0:
        return [], np.full(n, -1, dtype=np.int32)

    # --- 1. reverse adjacency: vein cell → vein cells flowing into it ---
    inflow_map: dict[int, list[int]] = {}
    for cell_id in vein_cells:
        cell_int: int = int(cell_id)
        r: int = int(receiver[cell_int])
        if r >= 0 and is_vein[r]:
            inflow_map.setdefault(r, []).append(cell_int)

    # --- 2. process in descending potential (sources first) ---
    order: Int32Array = np.argsort(a=potential_routed)[::-1].astype(np.int32)
    cell_vein_id: Int32Array = np.full(n, -1, dtype=np.int32)
    cell_owner: Int32Array = np.full(n, -1, dtype=np.int32)
    tributary_map: dict[int, int] = {}

    next_vein_id: int = 0
    vein_strength: dict[int, list[float]] = {}
    vein_channels: dict[int, list[Float64Array]] = {}
    vein_cells_map: dict[int, list[int]] = {}

    for cell_id in order:
        cell_id_int: int = int(cell_id)
        if not is_vein[cell_id_int]:
            continue
        if cell_owner[cell_id_int] >= 0:
            continue

        inflow: list[int] | None = inflow_map.get(cell_id_int)
        if not inflow:
            vein_id: int = next_vein_id
            next_vein_id += 1
            cell_owner[cell_id_int] = vein_id
            cell_vein_id[cell_id_int] = vein_id
            vein_strength[vein_id] = [float(magic_strength[cell_id_int])]
            vein_channels[vein_id] = [channels[cell_id_int]]
            vein_cells_map[vein_id] = [cell_id_int]
        else:
            best_vein_id: int = min(
                (int(cell_owner[inflow_cell]) for inflow_cell in inflow),
                key=lambda vid: (-max(vein_strength[vid]), vid),
            )
            cell_owner[cell_id_int] = best_vein_id
            cell_vein_id[cell_id_int] = best_vein_id
            vein_strength[best_vein_id].append(float(magic_strength[cell_id_int]))
            vein_channels[best_vein_id].append(channels[cell_id_int])
            vein_cells_map[best_vein_id].append(cell_id_int)
            for inflow_cell in inflow:
                vid = int(cell_owner[inflow_cell])
                if vid != best_vein_id:
                    tributary_map[vid] = best_vein_id

    # --- 3. build Vein objects, mouths, and pole links ---
    veins: list[Vein] = []
    for vein_id in range(next_vein_id):
        cells: list[int] = vein_cells_map[vein_id]
        if not cells:
            continue

        last_cell: int = cells[-1]
        r = int(receiver[last_cell])
        mouth: int = r if (r < 0 or not is_vein[r]) else last_cell

        mouth_nexus: int | None = None
        if mouth >= 0 and int(nexus_id[mouth]) >= 0:
            mouth_nexus = int(nexus_id[mouth])

        source_nexus: int = int(nexus_id[cells[0]])

        veins.append(
            Vein(
                id=vein_id,
                cells=cells,
                strength=np.array(vein_strength[vein_id], dtype=np.float64),
                channels=np.array(vein_channels[vein_id], dtype=np.float64),
                source_nexus=source_nexus,
                mouth_nexus=mouth_nexus,
                tributary_of=tributary_map.get(vein_id),
            )
        )

    return veins, cell_vein_id
