from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository
from src.worldgen.data import TileData


class TileRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_tiles(self, tiles: dict[tuple[int, int], TileData]) -> None:
        vertices = {}
        for (q, r), _tile in tiles.items():
            vertices[(q, r)] = self._base.create_vertex(
                type_name=VertexType.TILE,
                q=q,
                r=r,
            )

        for (q, r), tile in tiles.items():
            source = vertices[(q, r)]
            for nq, nr in tile.neighbors:
                self._base.create_edge(
                    type_name=EdgeType.ADJACENT,
                    source=source,
                    target=vertices[(nq, nr)],
                )
