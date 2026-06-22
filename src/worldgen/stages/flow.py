"""Flow stage: compute per-cell flow direction and stylized Manning speed.

Pipeline order: ``... → Discharge → Rivers → Lakes → Flow``
"""

import numpy as np

from src.worldgen.context import WorldContext
from src.worldgen.water.flow import compute_flow


class FlowStage:
    """Compute flow direction (flow_u/flow_v) and stylized speed (flow_speed).

    Phase 3 step 5: for each river/land cell, compute a unit direction
    vector pointing to the receiver and a Manning-flavored stylized speed
    derived from slope and discharge.

    Pipeline order: after LakesStage (is_lake must be populated).
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute flow direction and speed; write flow_u, flow_v, flow_speed."""
        # --- prerequisites ---
        site_field = ctx.geometry.sites
        receiver_field = ctx.fields.receiver
        if receiver_field is None:
            msg: str = "receiver must be set before FlowStage"
            raise RuntimeError(msg)
        receiver = receiver_field

        elevation_field = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before FlowStage"
            raise RuntimeError(msg)
        elevation = elevation_field

        discharge_field = ctx.fields.discharge
        if discharge_field is None:
            msg: str = "discharge must be set before FlowStage"
            raise RuntimeError(msg)
        discharge = discharge_field

        is_lake_field = ctx.fields.is_lake
        if is_lake_field is None:
            msg: str = "is_lake must be set before FlowStage"
            raise RuntimeError(msg)
        is_lake = is_lake_field

        is_river_field = ctx.fields.is_river

        # --- Compute flow ---
        flow_u, flow_v, flow_speed = compute_flow(
            site=site_field,
            receiver=receiver,
            elevation=elevation,
            discharge=discharge,
            is_lake=is_lake,
            is_river=is_river_field,
            width=ctx.geometry.width,
            height=ctx.geometry.height,
        )

        ctx.fields.flow_u = flow_u
        ctx.fields.flow_v = flow_v
        ctx.fields.flow_speed = flow_speed
