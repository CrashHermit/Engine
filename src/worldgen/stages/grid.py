from __future__ import annotations

from src.worldgen.context import WorldContext
from src.worldgen.geometry.grid_index import GridIndex


class GridStage:
    """Builds the gameplay tile grid and pre-computes neighbour references.

    Pipeline position: after ``BiomeStage``.
    """

    def run(self, ctx: WorldContext) -> WorldContext:
        size = ctx.config.size
        ctx.data.size = size
        ctx.data.grid.clear()

        grid_index = GridIndex(size)
        ctx.data = grid_index.build_base_grid(ctx.data)
        ctx.data = grid_index.build_neighbors(ctx.data)
        return ctx
