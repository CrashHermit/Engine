from src.worldgen.climate.moisture import compute_precipitation
from src.worldgen.config.worldgen_config import MoistureConfig
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array


class MoistureStage:
    """Geography-driven precipitation (a climate normal).

    Pipeline order: ``Insolation -> Wind -> OceanCurrent -> Temperature ->
    Moisture``.  Precipitation composes the latitude belt, continentality (coast
    distance) scaled by the wind-advected ``sst`` ocean source, orographic rain
    shadows, and a convergence perturbation — no iterative advection.  See
    ``docs/worldgen-precipitation-redesign-plan.md``.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute precipitation and write ``ctx.fields.precipitation``."""
        cfg: MoistureConfig = ctx.config.moisture

        # --- prerequisites ---
        latitude_field: Float64Array | None = ctx.fields.latitude
        if latitude_field is None:
            msg: str = "latitude must be set before MoistureStage"
            raise RuntimeError(msg)

        coast_distance_field: Float64Array | None = ctx.fields.coast_distance
        if coast_distance_field is None:
            msg = "coast_distance must be set before MoistureStage"
            raise RuntimeError(msg)

        sst_field: Float64Array | None = ctx.fields.sst
        if sst_field is None:
            msg = "sst must be set before MoistureStage"
            raise RuntimeError(msg)

        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg = "elevation must be set before MoistureStage"
            raise RuntimeError(msg)

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg = "is_land must be set before MoistureStage"
            raise RuntimeError(msg)

        wind_u_field: Float64Array | None = ctx.fields.wind_u
        if wind_u_field is None:
            msg = "wind_u must be set before MoistureStage"
            raise RuntimeError(msg)

        wind_v_field: Float64Array | None = ctx.fields.wind_v
        if wind_v_field is None:
            msg = "wind_v must be set before MoistureStage"
            raise RuntimeError(msg)

        convergence_field: Float64Array | None = ctx.fields.convergence
        if convergence_field is None:
            msg = "convergence must be set before MoistureStage"
            raise RuntimeError(msg)

        ctx.fields.precipitation = compute_precipitation(
            geometry=ctx.geometry,
            latitude=latitude_field,
            coast_distance=coast_distance_field,
            sst=sst_field,
            elevation=elevation_field,
            is_land=is_land_field,
            wind_u=wind_u_field,
            wind_v=wind_v_field,
            convergence=convergence_field,
            cfg=cfg,
        )
