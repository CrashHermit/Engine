from __future__ import annotations

from src.worldgen.context import WorldContext
from src.worldgen.geometry.periodic_voronoi import PeriodicVoronoi


class MeshStage:
    """Builds the periodic Voronoi mesh that all simulation layers run on.

    Pipeline position: first stage.
    """

    def run(self, ctx: WorldContext) -> WorldContext:
        cfg = ctx.config.mesh
        ctx.data.mesh = PeriodicVoronoi(
            width=cfg.width,
            height=cfg.height,
        ).build(
            seed=ctx.config.seed,
            cell_count=cfg.cell_count,
            lloyd_iterations=cfg.lloyd_iterations,
        )
        return ctx
