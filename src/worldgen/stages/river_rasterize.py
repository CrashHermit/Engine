from __future__ import annotations

import math

from src.worldgen.config.worldgen_config import HydrologyConfig
from src.worldgen.context import WorldContext


class RiverRasterizeStage:
    """Stamps river segments from the mesh network onto grid tiles.

    Draws each ``RiverSegment`` as a disk-swept line in grid coordinates,
    marking tiles ``is_river = True`` and recording the maximum flux.

    Pipeline position: after ``GridDeriveStage``.
    """

    def __init__(self, config: HydrologyConfig) -> None:
        self._config = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None or not ctx.data.rivers:
            return ctx

        size = ctx.data.size
        mesh = ctx.data.mesh
        cfg = self._config
        grid_lookup = ctx.data.grid

        for segment in ctx.data.rivers:
            sx, sy = segment.start
            ex, ey = segment.end
            flux = segment.flux

            radius = min(
                cfg.river_max_width,
                max(cfg.river_min_width, cfg.river_width_scale * math.sqrt(flux)),
            )

            gx0 = sx / mesh.width * size
            gy0 = sy / mesh.height * size
            gx1 = ex / mesh.width * size
            gy1 = ey / mesh.height * size

            length = math.hypot(gx1 - gx0, gy1 - gy0)
            steps = max(2, int(length / 0.5))

            for step in range(steps + 1):
                t = step / steps
                cx = gx0 + t * (gx1 - gx0)
                cy = gy0 + t * (gy1 - gy0)

                r_ceil = math.ceil(radius)
                ix_min = int(math.floor(cx - r_ceil))
                ix_max = int(math.floor(cx + r_ceil))
                iy_min = int(math.floor(cy - r_ceil))
                iy_max = int(math.floor(cy + r_ceil))

                for ix in range(ix_min, ix_max + 1):
                    for iy in range(iy_min, iy_max + 1):
                        if (ix - cx) ** 2 + (iy - cy) ** 2 > radius ** 2:
                            continue
                        wx = ix % size
                        wy = iy % size
                        tile = grid_lookup[wx * size + wy]
                        tile.position.is_river = True
                        if flux > tile.position.river_flux:
                            tile.position.river_flux = flux

        return ctx
