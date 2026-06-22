from src.worldgen.climate.temperature import compute_temperature
from src.worldgen.config.worldgen_config import TemperatureConfig
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array


class TemperatureStage:
    """Compute temperature from insolation, elevation, and maritime effects.

    Pipeline order: ``Insolation → Temperature → Wind → Moisture``
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

        # --- compute ---
        ctx.fields.temperature = compute_temperature(
            insolation=insolation,
            elevation=elevation,
            coast_distance=coast_distance,
            is_land=is_land,
            cfg=cfg,
        )
