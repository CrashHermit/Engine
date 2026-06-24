from src.worldgen.climate.ocean_current import compute_sst
from src.worldgen.config.worldgen_config import OceanCurrentConfig
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array


class OceanCurrentStage:
    """Compute wind-advected sea-surface temperature (toroidal currents).

    Pipeline order: ``Insolation → Wind → OceanCurrent → Temperature → Moisture``.
    Writes ``ctx.fields.sst``, which Temperature (maritime moderation) and
    Moisture (evaporation) then consume.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute SST and write ``ctx.fields.sst``."""
        cfg: OceanCurrentConfig = ctx.config.ocean_current

        # --- prerequisites ---
        insolation_field: Float64Array | None = ctx.fields.insolation
        if insolation_field is None:
            msg: str = "insolation must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        insolation: Float64Array = insolation_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg = "is_land must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        wind_u_field: Float64Array | None = ctx.fields.wind_u
        if wind_u_field is None:
            msg = "wind_u must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        wind_u: Float64Array = wind_u_field

        wind_v_field: Float64Array | None = ctx.fields.wind_v
        if wind_v_field is None:
            msg = "wind_v must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        wind_v: Float64Array = wind_v_field

        # --- compute ---
        ctx.fields.sst = compute_sst(
            geometry=ctx.geometry,
            wind_u=wind_u,
            wind_v=wind_v,
            insolation=insolation,
            is_land=is_land,
            cfg=cfg,
        )
