from __future__ import annotations

from src.worldgen.context import WorldContext
from src.worldgen.data import BiomeWeights
from src.worldgen.geometry.mesh_index import VoronoiMeshIndex


class GridDeriveStage:
    """Samples mesh fields onto each grid tile via nearest-cell lookup.

    Copies elevation, temperature, precipitation, wind, hydrology, savagery,
    alignment, biomes, and landmass data from the closest Voronoi cell to
    each grid tile.
    River flags are intentionally left false here; ``RiverRasterizeStage``
    stamps them afterwards from the segment network.

    Pipeline position: after ``GridStage``.
    """

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx

        mesh = ctx.data.mesh
        mesh_index = VoronoiMeshIndex(mesh)
        size = ctx.data.size

        for tile in ctx.data.grid:
            position = tile.position
            fx = (position.x + 0.5) / size * mesh.width
            fy = (position.y + 0.5) / size * mesh.height
            cell = mesh.cells[mesh_index.nearest_cell_id(fx, fy)]

            position.landmass_id = cell.landmass_id
            position.is_land = cell.is_land
            position.landmass_class = cell.landmass_class
            position.coast_distance = cell.coast_distance
            position.z = cell.z
            position.temperature = cell.temperature
            position.precipitation = cell.precipitation
            position.wind_u = cell.wind_u
            position.wind_v = cell.wind_v
            position.wind_magnitude = cell.wind_magnitude
            position.drainage_tiles = cell.drainage
            position.river_flux = cell.river_flux
            position.is_lake = cell.is_lake
            position.is_river = False
            position.savagery = cell.savagery
            position.alignment = cell.alignment
            position.biome_weights = [
                BiomeWeights(biome=entry.biome, weight=entry.weight)
                for entry in cell.biome_weights
            ]

        return ctx
