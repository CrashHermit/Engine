from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_BOUNDARY_UPLIFT, FIELD_UPLIFT_FLOOR
from src.worldgen.terrain.boundary_uplift import apply_boundary_uplift
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.types import Float64Array, Int32Array


class BoundaryUpliftStage:
    """Smear convergent/divergent plate-boundary intensity into ``uplift``."""

    def run(self, ctx: WorldContext) -> None:
        """Mutate ``ctx.fields.uplift`` with mountain belts and rift seams."""
        cfg: PlatesConfig = ctx.config.plates
        plate_id_field: Int32Array | None = ctx.fields.plate_id
        if plate_id_field is None:
            msg: str = "plate_id must be set before BoundaryUpliftStage"
            raise RuntimeError(msg)
        plate_id: Int32Array = plate_id_field
        uplift_field: Float64Array | None = ctx.fields.uplift
        if uplift_field is None:
            msg: str = "uplift must be set before BoundaryUpliftStage"
            raise RuntimeError(msg)
        uplift: Float64Array = uplift_field
        properties: PlateProperties | None = ctx.plate_properties
        if properties is None:
            msg: str = "plate_properties must be set before BoundaryUpliftStage"
            raise RuntimeError(msg)
        span: float = min(ctx.geometry.width, ctx.geometry.height)
        frequency: float = 4.0 / span
        belt_noise: FractalField = FractalField(
            sampler=ctx.noise_for("boundary_uplift"),
            field_id=FIELD_BOUNDARY_UPLIFT,
            octaves=3,
        )
        uplift_noise: FractalField = FractalField(
            sampler=ctx.noise_for("uplift_floor"),
            field_id=FIELD_UPLIFT_FLOOR,
            octaves=3,
        )
        apply_boundary_uplift(
            geometry=ctx.geometry,
            plate_id=plate_id,
            drift=properties.drift,
            uplift=uplift,
            config=cfg,
            belt_noise=belt_noise,
            uplift_noise=uplift_noise,
            frequency=frequency,
        )
