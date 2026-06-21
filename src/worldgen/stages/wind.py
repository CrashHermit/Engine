from src.worldgen.climate.wind import wind_belts
from src.worldgen.context import WorldContext
from src.worldgen.types import Float64Array
from src.worldgen.config.worldgen_config import WindConfig
from src.worldgen.noise.field import FractalField
from src.worldgen.climate.wind import elevation_gradient, deflect_wind


class WindStage:
    """Compute temperature from insolation, elevation, and maritime effects.

    Pipeline order: ``Insolation → Temperature → Wind → Moisture``
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute temperature and write ``ctx.fields.temperature``."""
        cfg: WindConfig = ctx.config.wind

        # --- prerequisites ---
        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before WindStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field
        wind_u = None
        wind_v = None

        wind = wind_belts(geometry=elevation, cfg=WindConfig, turbulence_u=, turbulence_v=)
