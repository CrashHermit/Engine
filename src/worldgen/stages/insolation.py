from src.worldgen.climate.insolation import insolation_field, latitude_field
from src.worldgen.config.worldgen_config import InsolationConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_INSOLATION_WOBBLE


class InsolationStage:
    """Compute the signed ``latitude`` driver and the insolation field.

    Pipeline order:
    ``Finalize → Insolation → Wind → OceanCurrent → Temperature → Moisture``
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute latitude + insolation; write both to ``ctx.fields``."""
        cfg: InsolationConfig = ctx.config.insolation

        # --- prerequisites ---
        geometry = ctx.geometry

        # --- optional wobble noise (warps the latitude lines) ---
        wobble_noise: FractalField | None = None
        if cfg.wobble > 0.0:
            wobble_noise = FractalField(
                sampler=ctx.noise_for("insolation_wobble"),
                field_id=FIELD_INSOLATION_WOBBLE,
                octaves=3,
            )

        # --- compute latitude first, then insolation from it ---
        latitude = latitude_field(
            geometry=geometry, cfg=cfg, wobble_noise=wobble_noise
        )
        ctx.fields.latitude = latitude
        ctx.fields.insolation = insolation_field(
            geometry=geometry, cfg=cfg, latitude=latitude
        )
