from src.worldgen.climate.wind import deflect_wind
from src.worldgen.climate.wind import elevation_gradient
from src.worldgen.climate.wind import wind_belts
from src.worldgen.config.worldgen_config import WindConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_WIND_U
from src.worldgen.noise.rng import FIELD_WIND_V
from src.worldgen.types import Float64Array


class WindStage:
    """Compute wind belts and terrain deflection.

    Pipeline order: ``Insolation → Temperature → Wind → Moisture``
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute wind fields and write ``ctx.fields.wind_u/v/magnitude``."""
        cfg: WindConfig = ctx.config.wind

        # --- prerequisites ---
        geometry = ctx.geometry

        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before WindStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        # --- turbulence noise fields (two independent sub-seeded sources) ---
        turbulence_u: FractalField = FractalField(
            sampler=ctx.noise_for("wind_u"),
            field_id=FIELD_WIND_U,
            octaves=3,
        )
        turbulence_v: FractalField = FractalField(
            sampler=ctx.noise_for("wind_v"),
            field_id=FIELD_WIND_V,
            octaves=3,
        )

        # --- step 3: wind belts ---
        wind_u, wind_v, wind_magnitude = wind_belts(
            geometry=geometry,
            cfg=cfg,
            turbulence_u=turbulence_u,
            turbulence_v=turbulence_v,
        )

        # --- step 4: terrain deflection ---
        grad_x, grad_y = elevation_gradient(
            geometry=ctx.geometry,
            elevation=elevation,
        )

        wind_u, wind_v, wind_magnitude = deflect_wind(
            wind_u=wind_u,
            wind_v=wind_v,
            grad_x=grad_x,
            grad_y=grad_y,
            cfg=cfg,
        )

        # --- write results ---
        ctx.fields.wind_u = wind_u
        ctx.fields.wind_v = wind_v
        ctx.fields.wind_magnitude = wind_magnitude
