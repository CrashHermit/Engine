from __future__ import annotations

import numpy as np

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_EROSION_INIT
from src.worldgen.terrain.erosion import diffuse, stream_power_pass
from src.worldgen.terrain.routing import (
    accumulate_drainage,
    compute_receivers,
    priority_flood,
)
from src.worldgen.types import Float64Array, Int32Array


class ErosionStage:
    """Tectonically-driven terrain: uplift-scaled initial height carved
    by stream-power erosion and hillslope diffusion.

    Replaces ``PlaceholderElevationStage``.
    Pipeline order: ``Mesh → Plates → BoundaryUplift → Erosion → …``
    """

    def run(self, ctx: WorldContext) -> None:
        """Run the full erosion loop and write ``elevation``."""
        cfg: ErosionConfig = ctx.config.erosion
        n: int = ctx.geometry.n_cells

        # --- prerequisites ---
        uplift_field: Float64Array | None = ctx.fields.uplift
        if uplift_field is None:
            msg: str = "uplift must be set before ErosionStage"
            raise RuntimeError(msg)
        uplift: Float64Array = uplift_field

        # --- initial elevation ---
        # z = uplift * initial_scale + small_noise
        noise_field: FractalField = FractalField(
            sampler=ctx.noise_for("erosion_init"),
            field_id=FIELD_EROSION_INIT,
            octaves=3,
        )

        sites: Float64Array = ctx.geometry.sites
        xs: Float64Array = sites[:, 0]
        ys: Float64Array = sites[:, 1]
        span: float = min(ctx.geometry.width, ctx.geometry.height)
        frequency: float = 4.0 / span

        noise: Float64Array = np.fromiter(
            (
                noise_field.sample(x=float(x_val), y=float(y_val), frequency=frequency)
                for x_val, y_val in zip(xs, ys)
            ),
            dtype=np.float64,
            count=n,
        )

        z: Float64Array = uplift * cfg.initial_scale + noise * cfg.initial_noise_amplitude

        # --- erosion loop ---
        if cfg.iterations <= 0:
            msg: str = "ErosionConfig.iterations must be > 0"
            raise ValueError(msg)

        for _iteration in range(cfg.iterations):
            # Determine provisional ocean cells (lowest percentile by current z).
            n_base: int = max(1, int(cfg.base_level_fraction * n))
            base_cells: Int32Array = np.argpartition(z, n_base)[:n_base].astype(np.int32)

            z_route: Float64Array = priority_flood(
                geometry=ctx.geometry,
                z=z,
                base_cells=base_cells,
            )
            receiver: Int32Array = compute_receivers(
                geometry=ctx.geometry,
                z_route=z_route,
            )
            drainage: Float64Array = accumulate_drainage(
                receiver=receiver,
                z_route=z_route,
            )
            stream_power_pass(
                z=z,
                z_route=z_route,
                receiver=receiver,
                drainage=drainage,
                uplift=uplift,
                geometry=ctx.geometry,
                cfg=cfg,
            )
            diffuse(
                z=z,
                geometry=ctx.geometry,
                cfg=cfg,
            )

        # --- store on ctx.fields before the last-iteration locals are dropped ---
        # (z_route, receiver, drainage are used inside the loop; the final
        # iteration's values are what flow downstream to FinalizeStage.)
        ctx.fields.elevation = z
        ctx.fields.z_route = z_route
        ctx.fields.receiver = receiver
        ctx.fields.drainage = drainage
