from datetime import datetime
from datetime import timezone
import uuid
from arcadedb_embedded.graph import Edge
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType, EdgeType
from database.repository.base import BaseRepository


class CharacterRepository(BaseRepository):

    def get_character(self, id: str) -> Vertex | None:
        return self.get_vertex(type_name=VertexType.CHARACTER, id=id)

    def create_character(self, name: str, description: str) -> Vertex:
        character: Vertex = self.create_vertex(
            type_name=VertexType.CHARACTER,
            name=name,
            id=str(uuid.uuid4()),
            description=description,
        )
        return character

    def get_or_create_character(self, id: str, name: str, description: str) -> Vertex:
        character: Vertex | None = self.get_character(id=id)
        if character is not None:
            return character

        return self.create_character(id=id, name=name, description=description)

    def get_or_create_attributes(self, character: Vertex) -> Vertex:
        attributes: Vertex | None = self.get_vertex(type_name=VertexType.ATTRIBUTES, name=character.get(name="name"))
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
