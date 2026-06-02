from arcadedb_embedded.graph import Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    # PROTOTYPE START
    def get_start_location(self) -> Vertex | None:
        worlds = self._base.list_vertices(VertexType.WORLD)
        if not worlds:
            return None
        edges = worlds[0].get_out_edges(EdgeType.HAS_START)
        return edges[0].get_in() if edges else None

    # PROTOTYPE END

    def create_world(
        self,
        name: str,
        description: str,
        size: int,
    ) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.WORLD,
            name=name,
            description=description,
            size=size,
        )
