from src.database.repository.base import BaseRepository
from arcadedb_embedded.graph import Vertex
from src.core.model.database import VertexType

class NPCRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_npc(self, name: str, description: str) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.NPC, name=name, description=description)

    def update_npc(self, npc: Vertex, name: str, description: str) -> None:
        pass

    def delete_npc(self, npc: Vertex) -> None:
        pass

    def get_npc(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.NPC, id=id)

    def list_npcs(self) -> list[Vertex]:
        return self._base.list_vertices(type_name=VertexType.NPC)

    def place_npc(self, npc: Vertex, location: Vertex) -> None:
        pass

    def move_npc(self, npc: Vertex, to_location: Vertex) -> None:
        pass

    def get_current_location(self, npc: Vertex) -> Vertex | None:
        pass

