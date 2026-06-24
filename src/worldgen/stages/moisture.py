from src.worldgen.climate.moisture import build_downwind, transport_moisture
from src.worldgen.config.worldgen_config import MoistureConfig
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array, Int32Array


class MoistureStage:
    """Advect ocean-sourced moisture downwind, raining it out.

    Pipeline order: ``Insolation → Temperature → Wind → Moisture``
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute precipitation and write ``ctx.fields.precipitation``."""
        cfg: MoistureConfig = ctx.config.moisture

        # --- prerequisites ---
        temperature_field: Float64Array | None = ctx.fields.temperature
        if temperature_field is None:
            msg: str = "temperature must be set before MoistureStage"
            raise RuntimeError(msg)
        temperature: Float64Array = temperature_field

        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before MoistureStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before MoistureStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        wind_u_field: Float64Array | None = ctx.fields.wind_u
        if wind_u_field is None:
            msg: str = "wind_u must be set before MoistureStage"
            raise RuntimeError(msg)
        wind_u: Float64Array = wind_u_field

        wind_v_field: Float64Array | None = ctx.fields.wind_v
        if wind_v_field is None:
            msg: str = "wind_v must be set before MoistureStage"
            raise RuntimeError(msg)
        wind_v: Float64Array = wind_v_field

        latitude_field: Float64Array | None = ctx.fields.latitude
        if latitude_field is None:
            msg = "latitude must be set before MoistureStage"
            raise RuntimeError(msg)
        latitude: Float64Array = latitude_field

        # --- step 5a: precompute downwind fan (once) ---
        downwind: tuple[Int32Array, Int32Array, Float64Array] = build_downwind(
            geometry=ctx.geometry,
            wind_u=wind_u,
            wind_v=wind_v,
        )

        # --- step 5b: advect moisture ---
        ctx.fields.precipitation = transport_moisture(
            geometry=ctx.geometry,
            downwind=downwind,
            temperature=temperature,
            elevation=elevation,
            is_land=is_land,
            latitude=latitude,
            cfg=cfg,
        )
