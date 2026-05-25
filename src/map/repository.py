import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository
from map.grid import TileData, generate_grid, hex_neighbors


class MapRepository(BaseRepository):
    def generate(self, rows: int, cols: int) -> None:
        """Create all tile vertices and their 6 adjacency edges in the database."""
        tiles = generate_grid(rows, cols)
        vertex_map: dict[tuple[int, int], Vertex] = {}

        with self.transaction():
            for tile in tiles:
                v = self.create_vertex(
                    VertexType.TILE,
                    row=tile.row,
                    col=tile.col,
                    elevation=0,
                    biome="",
                )
                vertex_map[(tile.row, tile.col)] = v

        with self.transaction():
            for tile in tiles:
                source = vertex_map[(tile.row, tile.col)]
                for direction, (nr, nc) in hex_neighbors(tile.row, tile.col, rows, cols).items():
                    target = vertex_map[(nr, nc)]
                    self.create_edge(EdgeType.ADJACENT, source=source, target=target, direction=direction)

    def get_tile(self, row: int, col: int) -> Vertex | None:
        results = list(
            self._database.query(f"SELECT FROM TILE WHERE row = {row} AND col = {col} LIMIT 1")
        )
        return results[0] if results else None
