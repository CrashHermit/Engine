from datetime import datetime
from datetime import timezone
import uuid
from arcadedb_embedded.graph import Edge
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType, EdgeType
from database.repository import user
from database.repository.base import BaseRepository


class CharacterRepository(BaseRepository):

    def get_user_characters(self) -> list[Vertex]:
        user: Vertex | None = self.get_user()

        edges: list[Edge] | None = self.get_vertex_out_edges(vertex=user, type_name=EdgeType.HAS_CHARACTER)

        return [edge.get_target() for edge in edges]

    def create_character(self, name: str, description: str) -> Vertex:
        user: Vertex | None = self.get_user()
        character: Vertex = self.create_vertex(
            type_name=VertexType.CHARACTER,
            name=name,
            description=description,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        self.create_edge(
            type_name=EdgeType.HAS_CHARACTER,
            source=user,
            target=character,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        return character

    def get_or_create_attributes(self, character: Vertex) -> Vertex:
        attributes: Vertex | None = self.get_vertex(type_name=VertexType.ATTRIBUTES, id=character.get(name="id"))
        if attributes is not None:
            return attributes

        attributes: Vertex = self.create_vertex(
            type_name=VertexType.ATTRIBUTES,
                name=character.get(name="name"),
            id=str(uuid.uuid4()),
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        
        self.create_edge(
            type_name=EdgeType.HAS_ATTRIBUTES,
            source=character,
            target=attributes,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        corpus: Vertex = self.create_vertex(
            type_name=VertexType.CORPUS,
            id=str(uuid.uuid4()),
            mens_score=0,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        self.create_edge(
            type_name=EdgeType.HAS_CORPUS,
            source=attributes,
            target=corpus,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        mens: Vertex = self.create_vertex(
            type_name=VertexType.MENS,
            id=str(uuid.uuid4()),
            mens_score=0,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        self.create_edge(
            type_name=EdgeType.HAS_MENS,
            source=attributes,
            target=mens,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        anima: Vertex = self.create_vertex(
            type_name=VertexType.ANIMA,
            id=str(uuid.uuid4()),
            anima_score=0,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        self.create_edge(
            type_name=EdgeType.HAS_ANIMA,
            source=attributes,
            target=anima,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        return attributes
