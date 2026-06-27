"""Rain-weighted discharge accumulation on the final terrain flow tree.

This is Phase 1's drainage loop with one change: each cell contributes
``precipitation[i]`` instead of ``1.0``.  Ocean cells are zeroed —
discharge is a land concept.
"""

import numpy as np

from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.workspace import Workspace
from src.worldgen.terrain.routing import (
    compute_receivers,
    priority_flood,
)


def accumulate_discharge(
    *,
    receiver: Int32Array,
    z_route: Float64Array,
    precipitation: Float64Array,
    is_land: BoolArray,
) -> Float64Array:
    """Accumulate rain-weighted water flow along the receiver flow tree.

    Every land cell contributes its own precipitation value and passes its
    accumulated total downstream to its receiver.  Processing from highest
    to lowest ``z_route`` guarantees every donor is complete before it hands
    off its total, so each cell is visited exactly once.

    Ocean cells receive zero discharge.

    Args:
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        z_route: Per-cell water-surface elevation from
            ``priority_flood`` (float64).  Used only for
            topological ordering.
        precipitation: Per-cell rainfall amount [0, 1].
        is_land: Boolean mask identifying land cells.

    Returns:
        discharge: Per-cell rain-weighted water flow (float64).
            Ocean cells are zeroed.
    """
    n: int = len(receiver)
    discharge: Float64Array = np.where(is_land, precipitation, 0.0)
    order: Int32Array = np.argsort(a=z_route)[::-1].astype(np.int32)

    for cell_id in order:
        r: int = int(receiver[cell_id])
        if r >= 0:
            discharge[r] += discharge[cell_id]

    # Ocean cells accumulate the totals of land cells draining into them;
    # zero them again — discharge is a land concept.
    discharge[~is_land] = 0.0

    return discharge


class DischargeStage:
    """Re-run flow routing on final terrain and compute rain-weighted discharge.

    Writes ``ctx.fields.z_route``, ``ctx.fields.receiver``, and
    ``ctx.fields.discharge``.  The fresh ``z_route``/``receiver`` are
    critical — downstream steps (rivers, lakes) depend on the flow tree
    matching the carved terrain, not the last erosion iteration's values.
    """

    reads: tuple[str, ...] = ("elevation", "is_land", "precipitation")
    writes: tuple[str, ...] = ("discharge", "receiver", "z_route")

    def run(self, ctx: Workspace) -> None:
        """Compute rain-weighted discharge and write flow tree + discharge."""
        n: int = ctx.geometry.n_cells

        # --- prerequisites ---
        elevation: Float64Array = ctx.fields.elevation

        is_land: BoolArray = ctx.fields.is_land

        precipitation: Float64Array = ctx.fields.precipitation

        # --- 1. Re-run priority-flood on final terrain ---
        # Determine base cells (lowest percentile by current z).  Use the same
        # base fraction the erosion loop used so the flow tree we route here
        # matches the one that carved the valleys.
        n_base: int = max(1, int(ctx.config.erosion.base_level_fraction * n))
        base_cells: Int32Array = np.argpartition(a=elevation, kth=n_base)[
            :n_base
        ].astype(np.int32)

        z_route: Float64Array = priority_flood(
            geometry=ctx.geometry,
            z=elevation,
            base_cells=base_cells,
        )
        ctx.fields.z_route = z_route

        # --- 2. Compute receivers on final terrain ---
        receiver: Int32Array = compute_receivers(
            geometry=ctx.geometry,
            z_route=z_route,
        )
        ctx.fields.receiver = receiver

        # --- 3. Accumulate rain-weighted discharge ---
        ctx.fields.discharge = accumulate_discharge(
            receiver=receiver,
            z_route=z_route,
            precipitation=precipitation,
            is_land=is_land,
        )
