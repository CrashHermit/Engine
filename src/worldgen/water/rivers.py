"""River classification and object extraction.

Step 2: ``classify_rivers`` — which cells carry a river based on discharge
percentile.  Step 3: ``extract_rivers`` — builds downstream-first River
objects (paths with identity, tributaries, mouths) from the receiver forest.
"""

import numpy as np

from src.worldgen.config.worldgen_config import RiverConfig
from src.core.model.environment.water.river import River
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.workspace import Workspace


def classify_rivers(
    *,
    discharge: Float64Array,
    is_land: BoolArray,
    is_lake: BoolArray,
    cfg: RiverConfig,
) -> BoolArray:
    """Classify river cells by discharge percentile.

    ``is_river = is_land & ~is_lake & (discharge >= threshold)``, where
    ``threshold`` is the ``(1 - cfg.river_fraction)`` quantile of land
    discharge.  This self-adjusts across world sizes and wetness levels.

    Args:
        discharge: Per-cell rain-weighted water flow (float64).
        is_land: Boolean mask identifying land cells.
        is_lake: Boolean mask identifying lake cells (water-filled depressions).
        cfg: River configuration with ``river_fraction`` (percentile, e.g.
            ``0.05`` → top 5 % of land discharge are rivers).

    Returns:
        is_river: Boolean array marking river cells.
    """
    land_discharge: Float64Array = discharge[is_land]
    n_land: int = int(np.sum(is_land))

    if n_land < 2:
        msg: str = "need at least 2 land cells to classify rivers"
        raise ValueError(msg)

    threshold: float = float(
        np.quantile(a=land_discharge, q=1.0 - cfg.river_fraction)
    )

    is_river: BoolArray = (
        is_land & ~is_lake & (discharge >= threshold)
    )

    return is_river


def extract_rivers(
    *,
    geometry: MeshGeometry,
    receiver: Int32Array,
    discharge: Float64Array,
    z_route: Float64Array,
    is_river: BoolArray,
    is_lake: BoolArray,
) -> tuple[list[River], Int32Array]:
    """Build downstream-first River objects from the receiver forest.

    The receiver array encodes a forest (each cell points at one parent).
    Rivers are the labeled paths through it:

    1. **Sources**: river cells with no river cell flowing into them
       (in-river-degree = 0).  Compute by counting, for each river cell,
       how many river cells have it as their receiver.
    2. Process river cells in **descending ``z_route``** order.  Each
       river cell asks: of the river cells flowing into me, whose
       discharge is largest? I continue *that* river; everyone else's
       river ends here with ``tributary_of = my_river_id``.  A river
       cell with no river inflow starts a new ``River``.
    3. A river ends (records its ``mouth``) when its receiver is
       ocean (``receiver == -1``), a lake cell, or a non-river cell.
    4. Write ``river_id`` per cell as we go; non-river cells stay ``-1``.

    Discharge ties at junctions are broken by cell id (lower id wins)
    so the result is deterministic.

    Args:
        geometry: Torus mesh (kept for API consistency; not used in this
            pure function since we only need the receiver tree).
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        discharge: Per-cell rain-weighted water flow.
        z_route: Per-cell water-surface elevation (for topological order).
        is_river: Boolean mask identifying river cells.
        is_lake: Boolean mask identifying lake cells.

    Returns:
        rivers: List of ``River`` objects (0-based ids).
        river_id: Per-cell river id (``-1`` = no river).
    """
    n: int = int(receiver.shape[0])
    river_cells: Int32Array = np.flatnonzero(is_river).astype(np.int32)
    n_river: int = len(river_cells)

    if n_river == 0:
        return [], np.full(n, -1, dtype=np.int32)

    # --- 1. Build reverse adjacency: river_cell → list of river cells
    #    that flow into it (pre-computed, O(n_river) total) ---
    inflow_map: dict[int, list[int]] = {}
    for cell_id in river_cells:
        cell_int: int = int(cell_id)
        r: int = int(receiver[cell_int])
        if r >= 0 and is_river[r]:
            if r not in inflow_map:
                inflow_map[r] = []
            inflow_map[r].append(cell_int)

    # --- 2. Process in descending z_route (topological: sources first) ---
    order: Int32Array = np.argsort(a=z_route)[::-1].astype(np.int32)

    cell_river_id: Int32Array = np.full(n, -1, dtype=np.int32)

    # Per-cell owner (which river object owns this cell)
    cell_owner: Int32Array = np.full(n, -1, dtype=np.int32)

    # tributary_of[tributary_river_id] = trunk_river_id
    tributary_map: dict[int, int] = {}

    next_river_id: int = 0
    # Per-river accumulation
    river_discharge: dict[int, list[float]] = {}
    river_cells_map: dict[int, list[int]] = {}

    for cell_id in order:
        cell_id_int: int = int(cell_id)
        if not is_river[cell_id_int]:
            continue
        if cell_owner[cell_id_int] >= 0:
            # Already assigned
            continue

        # Find river cells flowing into this cell
        inflow: list[int] | None = inflow_map.get(cell_id_int)

        if not inflow:
            # Source: start a new river
            river_id: int = next_river_id
            next_river_id += 1
            cell_owner[cell_id_int] = river_id
            cell_river_id[cell_id_int] = river_id
            river_discharge[river_id] = [float(discharge[cell_id_int])]
            river_cells_map[river_id] = [cell_id_int]
        else:
            # Junction: pick the inflow river with largest discharge.
            # Break ties by river id (lower wins → deterministic).
            best_river_id: int = min(
                (int(cell_owner[inflow_cell]) for inflow_cell in inflow),
                key=lambda rid: (-max(river_discharge[rid]), rid),
            )
            # Continue the best river
            cell_owner[cell_id_int] = best_river_id
            cell_river_id[cell_id_int] = best_river_id
            river_discharge[best_river_id].append(float(discharge[cell_id_int]))
            river_cells_map[best_river_id].append(cell_id_int)

            # Record tributaries
            for inflow_cell in inflow:
                rid = int(cell_owner[inflow_cell])
                if rid != best_river_id:
                    tributary_map[rid] = best_river_id

    # --- 3. Build River objects and determine mouths ---
    rivers: list[River] = []
    for river_id in range(next_river_id):
        cells: list[int] = river_cells_map[river_id]
        if not cells:
            continue

        # Mouth: receiver of last cell.
        # If receiver is -1 (ocean), a lake cell, or non-river → mouth = receiver.
        # If receiver is another river cell → tributary, mouth = last cell itself.
        last_cell: int = cells[-1]
        r: int = int(receiver[last_cell])
        if r < 0 or is_lake[r] or not is_river[r]:
            mouth: int = r
        else:
            mouth = last_cell

        discharge_along: tuple[float, ...] = tuple(
            float(value) for value in river_discharge[river_id]
        )

        tributary_of: int | None = tributary_map.get(river_id)

        rivers.append(
            River(
                id=river_id,
                cells=cells,
                discharge=discharge_along,
                mouth=mouth,
                tributary_of=tributary_of,
            )
        )

    return rivers, cell_river_id


class RiversStage:
    """Classify river cells, extract River objects, write river_id to fields.

    Phase 3 step 2: ``classify_rivers`` — percentile threshold on land
    discharge.  Phase 3 step 3: ``extract_rivers`` — build downstream-first
    River objects from the receiver forest.

    Lake exclusion uses the ``is_lake`` field when LakesStage has already
    populated it; in canonical pipeline order (Rivers before Lakes) it has
    not, so the stage derives the lake-mask stand-in ``is_land & (z_route > z
    + epsilon)`` — the same mask LakesStage computes.  This keeps river cells
    out of water-filled depressions and lets rivers terminate at lake cells.

    Pipeline order: after DischargeStage, before LakesStage.
    """

    reads: tuple[str, ...] = ("discharge", "elevation", "is_lake", "is_land", "is_river", "receiver", "z_filled", "z_route")
    writes: tuple[str, ...] = ("is_river", "river_id")
    reads_optional: tuple[str, ...] = ("is_lake",)

    def run(self, ctx: Workspace) -> None:
        """Classify river cells, extract rivers, write river_id and ctx.outputs.rivers."""
        cfg: RiverConfig = ctx.config.river

        # --- prerequisites ---
        discharge: Float64Array = ctx.fields.discharge

        is_land: BoolArray = ctx.fields.is_land

        receiver: Int32Array = ctx.fields.receiver

        z_route: Float64Array = ctx.fields.z_route

        is_lake_field: BoolArray | None = ctx.fields.is_lake
        if is_lake_field is None:
            # LakesStage runs after this stage, so is_lake is not written yet.
            # Use the lake-mask stand-in `z_filled > z + epsilon` — identical to
            # the mask LakesStage will compute — so the two stages agree.  Read
            # the physical spill surface, not z_route, whose flat-draining bias
            # would over-detect lakes (see priority_flood / extract_lakes).
            elevation_field: Float64Array = ctx.fields.elevation
            z_filled: Float64Array = ctx.fields.z_filled
            is_lake: BoolArray = is_land & (
                z_filled > elevation_field + ctx.config.lake.epsilon
            )
        else:
            is_lake: BoolArray = is_lake_field

        # --- Step 2: classify river cells ---
        ctx.fields.is_river = classify_rivers(
            discharge=discharge,
            is_land=is_land,
            is_lake=is_lake,
            cfg=cfg,
        )

        # --- Step 3: extract River objects ---
        # Initialize river_id to -1 (no river) before stamping.
        n: int = ctx.geometry.n_cells
        ctx.fields.river_id = np.full(n, -1, dtype=np.int32)

        rivers, river_id = extract_rivers(
            geometry=ctx.geometry,
            receiver=receiver,
            discharge=discharge,
            z_route=z_route,
            is_river=ctx.fields.is_river,
            is_lake=is_lake,
        )
        ctx.outputs.rivers = rivers

        # Stamp river_id into fields
        ctx.fields.river_id = river_id
