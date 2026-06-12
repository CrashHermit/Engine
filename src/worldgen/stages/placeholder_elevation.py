from __future__ import annotations

import numpy as np

from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_ELEVATION


class PlaceholderElevationStage:
    """Temporary noise elevation until Phase 1 terrain replaces it."""

    def run(self, ctx: WorldContext) -> None:
        span: float = min(ctx.geometry.width, ctx.geometry.height)
        frequency: float = 4.0 / span

        field: FractalField = FractalField(
            sampler=ctx.noise_for(name="elevation"),
            field_id=FIELD_ELEVATION,
            octaves=3,
        )

        xs: Float64Array = ctx.geometry.sites[:, 0]
        ys: Float64Array = ctx.geometry.sites[:, 1]
        z: Float64Array = np.fromiter(
            iter=(field.sample(x=float(x), y=float(y), frequency=frequency) for x, y in zip(xs, ys)),
            dtype=np.float64,
            count=ctx.geometry.n_cells,
        )

        z_min: np.float64 = z.min()
        z_max: np.float64 = z.max()
        ctx.fields.elevation: Float64Array = (z - z_min) / (z_max - z_min)
        ctx.fields.is_land: BoolArray = ctx.fields.elevation > 0.6
