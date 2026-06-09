from __future__ import annotations

from src.worldgen.config.worldgen_config import AlignmentConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.sampler import FIELD_ALIGNMENT


class AlignmentStage:
    """Generates smooth alignment values on the mesh.

    Output is in ``[-1, 1]`` where negative values are chaotic/dark and
    positive values are ordered/holy.  Pipeline position: after
    ``SavageryStage``.
    """

    def __init__(self, config: AlignmentConfig) -> None:
        self._config = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx

        mesh = ctx.data.mesh
        cfg = self._config
        field = FractalField(ctx.sampler, FIELD_ALIGNMENT, octaves=3)

        for cell in mesh.cells:
            x, y = cell.site
            raw = field.sample(x, y, cfg.noise_scale)
            value = (raw + 1.0) * 0.5
            value = value * cfg.blend_weight + 0.5 * (1.0 - cfg.blend_weight)
            signed = (value * 2.0 - 1.0) * cfg.amplitude
            cell.alignment = max(-1.0, min(1.0, signed))

        return ctx
