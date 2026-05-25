from arcadedb_embedded.graph import Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository
from map.config import GridConfig, HeightmapConfig, RiverConfig
from map.grid import generate_grid, hex_neighbors
from map.heightmap import generate_heightmap
from map.river import compute_flow, compute_flux


class MapRepository(BaseRepository):
    def generate(
        self,
        grid: GridConfig | None = None,
        heightmap: HeightmapConfig | None = None,
    ) -> None:
        """Create all tile vertices and their 6 adjacency edges in the database."""
        grid = grid or GridConfig()
        heightmap = heightmap or HeightmapConfig()

        tiles = generate_grid(grid.rows, grid.cols)
        elevations = generate_heightmap(tiles, grid.rows, grid.cols, heightmap)

        vertex_map: dict[tuple[int, int], Vertex] = {}
        with self.transaction():
            for tile in tiles:
                elevation = elevations[(tile.row, tile.col)]
                v = self.create_vertex(
                    VertexType.TILE,
                    row=tile.row,
                    col=tile.col,
                    elevation=elevation,
                    flux=0,
                    biome="ocean" if elevation < heightmap.sea_level else "",
                )
                vertex_map[(tile.row, tile.col)] = v

        with self.transaction():
            for tile in tiles:
                source = vertex_map[(tile.row, tile.col)]
                for direction, (nr, nc) in hex_neighbors(tile.row, tile.col, grid.rows, grid.cols).items():
                    target = vertex_map[(nr, nc)]
                    self.create_edge(EdgeType.ADJACENT, source=source, target=target, direction=direction)

    def generate_rivers(
        self,
        grid: GridConfig | None = None,
        heightmap: HeightmapConfig | None = None,
        rivers: RiverConfig | None = None,
    ) -> None:
        """
        Compute river flow and flux, write flux onto each tile, and create
        FLOWS_TO edges so river paths are directly traversable in the graph.
        """
        grid = grid or GridConfig()
        heightmap = heightmap or HeightmapConfig()
        rivers = rivers or RiverConfig()

        tiles = generate_grid(grid.rows, grid.cols)
        elevations = generate_heightmap(tiles, grid.rows, grid.cols, heightmap)

        flow_to = compute_flow(tiles, elevations, grid.rows, grid.cols, heightmap.sea_level)
        flux = compute_flux(tiles, flow_to, rivers)

        # Write flux back onto tile vertices
        with self.transaction():
            for tile in tiles:
                pos = (tile.row, tile.col)
                tile_flux = flux.get(pos, 0)
                if tile_flux < rivers.min_flux:
                    continue
                vertex = self.get_tile(tile.row, tile.col)
                if vertex is not None:
                    self.update_vertex(vertex, flux=tile_flux)

        # Create FLOWS_TO edges for tiles above the min_flux threshold
        with self.transaction():
            for tile in tiles:
                pos = (tile.row, tile.col)
                if flux.get(pos, 0) < rivers.min_flux:
                    continue
                downstream = flow_to[pos]
                if downstream is None:
                    continue
                source_v = self.get_tile(tile.row, tile.col)
                target_v = self.get_tile(*downstream)
                if source_v is not None and target_v is not None:
                    self.create_edge(EdgeType.FLOWS_TO, source=source_v, target=target_v)

    def get_tile(self, row: int, col: int) -> Vertex | None:
        results = list(
            self._database.query(f"SELECT FROM TILE WHERE row = {row} AND col = {col} LIMIT 1")
        )
        return results[0] if results else None
