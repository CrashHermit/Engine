from arcadedb_embedded.graph import Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository
from map.config import GridConfig, HeightmapConfig
from map.grid import generate_grid, hex_neighbors
from map.heightmap import generate_heightmap


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
                    biome="ocean" if elevation < heightmap.sea_level else "",
                )
                vertex_map[(tile.row, tile.col)] = v

        with self.transaction():
            for tile in tiles:
                source = vertex_map[(tile.row, tile.col)]
                for direction, (nr, nc) in hex_neighbors(tile.row, tile.col, grid.rows, grid.cols).items():
                    target = vertex_map[(nr, nc)]
                    self.create_edge(EdgeType.ADJACENT, source=source, target=target, direction=direction)

    def get_tile(self, row: int, col: int) -> Vertex | None:
        results = list(
            self._database.query(f"SELECT FROM TILE WHERE row = {row} AND col = {col} LIMIT 1")
        )
        return results[0] if results else None
