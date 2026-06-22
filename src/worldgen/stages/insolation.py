from src.worldgen.climate.insolation import insolation_field
from src.worldgen.config.worldgen_config import InsolationConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_INSOLATION_WOBBLE


class InsolationStage:
    """Compute the authored energy (insolation) field.

    Pipeline order: ``Finalize → Insolation → Temperature → Wind → Moisture``
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute insolation and write ``ctx.fields.insolation``."""
        cfg: InsolationConfig = ctx.config.insolation

        # --- prerequisites ---
        geometry = ctx.geometry

        # --- optional wobble noise ---
        wobble_noise: FractalField | None = None
        if cfg.wobble > 0.0:
            wobble_noise = FractalField(
                sampler=ctx.noise_for("insolation_wobble"),
                field_id=FIELD_INSOLATION_WOBBLE,
                octaves=3,
            )

        # --- compute ---
        ctx.fields.insolation = insolation_field(
            geometry=geometry,
            cfg=cfg,
            wobble_noise=wobble_noise,
        )
