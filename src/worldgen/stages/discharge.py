"""Discharge stage: re-route on final terrain, accumulate rain-weighted flow.

Pipeline order: ``... → Moisture → Discharge → Rivers → Lakes → Flow``
"""

import numpy as np

from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.water.discharge import accumulate_discharge
from src.worldgen.terrain.routing import (
    compute_receivers,
    priority_flood,
)


class DischargeStage:
    """Re-run flow routing on final terrain and compute rain-weighted discharge.

    Writes ``ctx.fields.z_route``, ``ctx.fields.receiver``, and
    ``ctx.fields.discharge``.  The fresh ``z_route``/``receiver`` are
    critical — downstream steps (rivers, lakes) depend on the flow tree
    matching the carved terrain, not the last erosion iteration's values.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute rain-weighted discharge and write flow tree + discharge."""
        n: int = ctx.geometry.n_cells

        # --- prerequisites ---
        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before DischargeStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before DischargeStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        precipitation_field: Float64Array | None = ctx.fields.precipitation
        if precipitation_field is None:
            msg: str = "precipitation must be set before DischargeStage"
            raise RuntimeError(msg)
        precipitation: Float64Array = precipitation_field

        # --- 1. Re-run priority-flood on final terrain ---
        # Determine base cells (lowest percentile by current z).
        n_base: int = max(1, int(0.1 * n))
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
