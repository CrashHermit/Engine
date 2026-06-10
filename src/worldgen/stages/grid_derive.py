from __future__ import annotations

from copy import deepcopy

from src.worldgen.context import WorldContext
from src.worldgen.geometry.mesh_index import VoronoiMeshIndex


class GridDeriveStage:
    """Samples the mesh attribute bundle onto each grid tile.

    Copies the closest Voronoi cell's entire ``CellEnvironment`` onto each
    grid tile, so the grid is a faithful rasterisation of the mesh.
    River flags are intentionally cleared here; ``RiverRasterizeStage`` stamps
    them afterwards from the segment network.

    Pipeline position: after ``GridStage``.
    """

    def run(self, ctx: WorldContext) -> None:
        mesh = ctx.data.mesh
        mesh_index = VoronoiMeshIndex(mesh)
        size = ctx.config.size

        for tile in ctx.data.grid:
            fx = (tile.x + 0.5) / size * mesh.width
            fy = (tile.y + 0.5) / size * mesh.height
            cell = mesh.cells[mesh_index.nearest_cell_id(fx, fy)]

            tile.env = deepcopy(cell.env)
            tile.env.hydrology.is_river = False
