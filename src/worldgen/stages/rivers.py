"""Rivers stage: classify river cells, extract River objects, stamp river_id.

Pipeline order: ``... → Discharge → Rivers → Lakes → Flow``
"""

import numpy as np

from src.worldgen.config.worldgen_config import RiverConfig
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.water.rivers import classify_rivers, extract_rivers


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

    def run(self, ctx: WorldContext) -> None:
        """Classify river cells, extract rivers, write river_id and ctx.rivers."""
        cfg: RiverConfig = ctx.config.river

        # --- prerequisites ---
        discharge_field: Float64Array | None = ctx.fields.discharge
        if discharge_field is None:
            msg: str = "discharge must be set before RiversStage"
            raise RuntimeError(msg)
        discharge: Float64Array = discharge_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before RiversStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        receiver_field: Int32Array | None = ctx.fields.receiver
        if receiver_field is None:
            msg: str = "receiver must be set before RiversStage"
            raise RuntimeError(msg)
        receiver: Int32Array = receiver_field

        z_route_field: Float64Array | None = ctx.fields.z_route
        if z_route_field is None:
            msg: str = "z_route must be set before RiversStage"
            raise RuntimeError(msg)
        z_route: Float64Array = z_route_field

        is_lake_field: BoolArray | None = ctx.fields.is_lake
        if is_lake_field is None:
            # LakesStage runs after this stage, so is_lake is not written yet.
            # Use the lake-mask stand-in `z_route > z + epsilon` — identical to
            # the mask LakesStage will compute — so the two stages agree.
            elevation_field: Float64Array | None = ctx.fields.elevation
            if elevation_field is None:
                msg: str = "elevation must be set before RiversStage"
                raise RuntimeError(msg)
            is_lake: BoolArray = is_land & (
                z_route > elevation_field + ctx.config.lake.epsilon
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
        ctx.rivers = rivers

        # Stamp river_id into fields
        ctx.fields.river_id = river_id
