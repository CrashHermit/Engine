import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository

# Outgoing directions per tile: east, north, northeast
# Each tile receives the 3 complementary incoming edges from west, south, southwest
_OUTGOING_DIRECTIONS = [(1, 0), (0, 1), (1, 1)]


class MapGenerator:
    def __init__(self, size: int, database: arcadedb.Database) -> None:
        self._size = size
        self._repo = BaseRepository(database)

    def generate(self) -> dict[tuple[int, int], Vertex]:
        size = self._size
        tiles: dict[tuple[int, int], Vertex] = {}

        with self._repo.transaction():
            for q in range(size):
                for r in range(size):
                    tile = self._repo.create_vertex(VertexType.TILE, q=q, r=r)
                    tiles[(q, r)] = tile

            for (q, r), tile in tiles.items():
                for dq, dr in _OUTGOING_DIRECTIONS:
                    nq = (q + dq) % size
                    nr = (r + dr) % size
                    self._repo.create_edge(EdgeType.ADJACENT, tile, tiles[(nq, nr)])

        return tiles
