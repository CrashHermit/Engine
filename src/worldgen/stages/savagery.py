"""Savagery stage: legible danger from geography.

Pipeline order: ``... → Flow → Savagery → Leylines → Biomes``
"""

from src.worldgen.config.worldgen_config import SavageryConfig
from src.worldgen.context import WorldContext
from src.worldgen.geometry.field_ops import diffuse
from src.worldgen.magic.savagery import compute_savagery
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_SAVAGERY
from src.worldgen.types import Float64Array


class SavageryStage:
    """Blend remoteness, harshness, ruggedness, and noise into ``savagery``.

    Pipeline order: after the water stages, before Leylines.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute savagery and write ``ctx.fields.savagery``."""
        cfg: SavageryConfig = ctx.config.savagery
        geometry = ctx.geometry

        # --- prerequisites ---
        coast_distance_field: Float64Array | None = ctx.fields.coast_distance
        if coast_distance_field is None:
            msg: str = "coast_distance must be set before SavageryStage"
            raise RuntimeError(msg)
        coast_distance: Float64Array = coast_distance_field

        temperature_field: Float64Array | None = ctx.fields.temperature
        if temperature_field is None:
            msg = "temperature must be set before SavageryStage"
            raise RuntimeError(msg)
        temperature: Float64Array = temperature_field

        precipitation_field: Float64Array | None = ctx.fields.precipitation
        if precipitation_field is None:
            msg = "precipitation must be set before SavageryStage"
            raise RuntimeError(msg)
        precipitation: Float64Array = precipitation_field

        slope_field: Float64Array | None = ctx.fields.slope
        if slope_field is None:
            msg = "slope must be set before SavageryStage"
            raise RuntimeError(msg)
        slope: Float64Array = slope_field

        volcanism_field: Float64Array | None = ctx.fields.volcanism
        if volcanism_field is None:
            msg = "volcanism must be set before SavageryStage"
            raise RuntimeError(msg)
        volcanism: Float64Array = volcanism_field

        # --- surprise noise ---
        noise_field: FractalField = FractalField(
            sampler=ctx.noise_for("savagery"),
            field_id=FIELD_SAVAGERY,
            octaves=4,
        )
        frequency: float = cfg.noise_frequency
        noise: Float64Array = noise_field.sample_array(
            xs=geometry.sites[:, 0], ys=geometry.sites[:, 1], frequency=frequency
        )

        savagery: Float64Array = compute_savagery(
            coast_distance=coast_distance,
            temperature=temperature,
            precipitation=precipitation,
            slope=slope,
            noise=noise,
            volcanism=volcanism,
            cfg=cfg,
        )

        # Savagery is consumed as discrete bands, so single-tile flips read as
        # confetti.  A light Laplacian smooth removes them while keeping the
        # intentional noise-term texture (it is defined on every cell, so smooth
        # unmasked).
        ctx.fields.savagery = diffuse(
            geometry=geometry,
            field=savagery,
            strength=cfg.smoothing_strength,
            passes=cfg.smoothing_passes,
        )
