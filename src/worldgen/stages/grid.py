from __future__ import annotations

from src.worldgen.context import WorldContext
from src.worldgen.geometry.grid_index import GridIndex


class GridStage:
    """Builds the gameplay tile grid.

    Pipeline position: after ``AlignmentStage``.
    """

    def run(self, ctx: WorldContext) -> None:
        ctx.data.grid.clear()

        grid_index = GridIndex(ctx.config.size)
        grid_index.build_base_grid(ctx.data)
