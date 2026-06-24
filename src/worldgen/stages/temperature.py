from src.worldgen.climate.ocean_current import maritime_sst_onshore
from src.worldgen.climate.temperature import compute_temperature
from src.worldgen.config.worldgen_config import TemperatureConfig
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array


class TemperatureStage:
    """Compute temperature from insolation, elevation, and maritime effects.

    Pipeline order: ``Insolation → Wind → OceanCurrent → Temperature → Moisture``.
    Consumes the SST field from ``OceanCurrentStage``: ocean cells take their
    SST directly and coasts moderate toward the wind-borne ocean SST.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute temperature and write ``ctx.fields.temperature``."""
        cfg: TemperatureConfig = ctx.config.temperature

        # --- prerequisites ---
        insolation_field: Float64Array | None = ctx.fields.insolation
        if insolation_field is None:
            msg: str = "insolation must be set before TemperatureStage"
            raise RuntimeError(msg)
        insolation: Float64Array = insolation_field

        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before TemperatureStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        coast_distance_field: Float64Array | None = ctx.fields.coast_distance
        if coast_distance_field is None:
            msg: str = "coast_distance must be set before TemperatureStage"
            raise RuntimeError(msg)
        coast_distance: Float64Array = coast_distance_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before TemperatureStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        sst_field: Float64Array | None = ctx.fields.sst
        if sst_field is None:
            msg = "sst must be set before TemperatureStage"
            raise RuntimeError(msg)
        sst: Float64Array = sst_field

        wind_u_field: Float64Array | None = ctx.fields.wind_u
        wind_v_field: Float64Array | None = ctx.fields.wind_v
        if wind_u_field is None or wind_v_field is None:
            msg = "wind must be set before TemperatureStage"
            raise RuntimeError(msg)

        # --- carry ocean SST onshore along the wind for maritime moderation ---
        maritime_sst: Float64Array = maritime_sst_onshore(
            geometry=ctx.geometry,
            wind_u=wind_u_field,
            wind_v=wind_v_field,
            sst=sst,
            insolation=insolation,
            is_land=is_land,
            reach=cfg.maritime_reach,
        )

        # --- compute ---
        ctx.fields.temperature = compute_temperature(
            insolation=insolation,
            elevation=elevation,
            coast_distance=coast_distance,
            is_land=is_land,
            sst=sst,
            maritime_sst=maritime_sst,
            cfg=cfg,
        )
