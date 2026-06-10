from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from src.worldgen.context import WorldContext
from src.worldgen.model import CellEnvironment
from src.worldgen.noise.field import FractalField


class ScalarFieldConfig(Protocol):
    """Structural config shared by every smooth scalar-field stage."""

    noise_scale: float
    blend_weight: float
    amplitude: float


class ScalarFieldStage:
    """Generates a smooth scalar field on the mesh from fractal noise.

    Shared by savagery and alignment (and any future smooth per-cell scalar):
    sample a fractal field, remap to ``[0, 1]``, blend toward the neutral
    midpoint, and scale by amplitude. When ``signed`` the result is remapped
    to ``[-1, 1]``; otherwise it stays in ``[0, 1]``. The final value is
    written through ``assign``.
    """

    def __init__(
        self,
        config: ScalarFieldConfig,
        field_id: int,
        *,
        signed: bool,
        assign: Callable[[CellEnvironment, float], None],
    ) -> None:
        self._config = config
        self._field_id = field_id
        self._signed = signed
        self._assign = assign

    def run(self, ctx: WorldContext) -> None:
        cfg = self._config
        field = FractalField(ctx.sampler, self._field_id, octaves=3)

        for cell in ctx.data.mesh.cells:
            x, y = cell.site
            raw = field.sample(x, y, cfg.noise_scale)
            value = (raw + 1.0) * 0.5
            value = value * cfg.blend_weight + 0.5 * (1.0 - cfg.blend_weight)
            if self._signed:
                out = max(-1.0, min(1.0, (value * 2.0 - 1.0) * cfg.amplitude))
            else:
                out = max(0.0, min(1.0, value * cfg.amplitude))
            self._assign(cell.env, out)
