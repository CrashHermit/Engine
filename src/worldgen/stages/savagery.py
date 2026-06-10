from __future__ import annotations

from src.worldgen.config.worldgen_config import SavageryConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.sampler import FIELD_SAVAGERY


class SavageryStage:
    """Generates smooth savagery values on the mesh.

    Output is in ``[0, 1]`` where low values are tame and high values are
    savage.  Pipeline position: after ``ClimateStage``.
    """

    def __init__(self, config: SavageryConfig) -> None:
        self._config = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx

        mesh = ctx.data.mesh
        cfg = self._config
        field = FractalField(ctx.sampler, FIELD_SAVAGERY, octaves=3)

        for cell in mesh.cells:
            x, y = cell.site
            raw = field.sample(x, y, cfg.noise_scale)
            value = (raw + 1.0) * 0.5
            value = value * cfg.blend_weight + 0.5 * (1.0 - cfg.blend_weight)
            cell.savagery = max(0.0, min(1.0, value * cfg.amplitude))

        return ctx
