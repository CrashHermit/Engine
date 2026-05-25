from typing import Any
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType, EdgeType
from core.model.part import Shape, Status, SizeScale
from database.repository.character import CharacterRepository

class PartRepository(CharacterRepository):
    def add_part(
        self,
        character: Vertex,
        name: str,
        length: SizeScale,
        width: SizeScale,
        height: SizeScale,
        shape: Shape,
        status: Status = Status.NORMAL,
        description: str = "",
    ) -> Vertex:
        part: Vertex = self.create_vertex(
            type_name=VertexType.PART,
            name=name,
            length=length,
            width=width,
            height=height,
            shape=shape,
            status=status,
            description=description,
        )
        self.create_edge(
            type_name=EdgeType.HAS_PART,
            source=character,
            target=part,
        )
        return part

    def attach(self, source: Vertex, target: Vertex) -> None:
        self.create_edge(
            type_name=EdgeType.ATTACHED_TO,
            source=source,
            target=target,
        )

    def add_source(self, part: Vertex) -> Vertex:
        source: Vertex = self.create_vertex(
            type_name=VertexType.SOURCE
        )
        self.create_edge(
                type_name=EdgeType.IS_SOURCE,
                source=part,
                target=source,
            )
        return source

    def add_manipulator(self, part: Vertex) -> Vertex:
        manipulator: Vertex = self.create_vertex(
            type_name=VertexType.MANIPULATOR,
        )
        self.create_edge(
                type_name=EdgeType.IS_MANIPULATOR,
                source=part,
                target=manipulator,
            )
        return manipulator

    def add_controllable(self, part: Vertex) -> Vertex:
        controllable: Vertex = self.create_vertex(
            type_name=VertexType.CONTROLLABLE,
        )
        self.create_edge(
                type_name=EdgeType.IS_CONTROLLABLE,
                source=part,
                target=controllable,
            )
        return controllable

    def add_opening(self, part: Vertex) -> Vertex:
        opening: Vertex = self.create_vertex(
            type_name=VertexType.OPENING,
        )
        self.create_edge(
            type_name=EdgeType.IS_OPENING,
            source=part,
            target=opening,
        )
        return opening

    def add_channel(self, part: Vertex) -> Vertex:
        channel: Vertex = self.create_vertex(
            type_name=VertexType.CHANNEL,
        )
        self.create_edge(
                type_name=EdgeType.IS_CHANNEL,
                source=part,
                target=channel,
            )
        return channel

    def add_storage(self, part: Vertex) -> Vertex:
        storage: Vertex = self.create_vertex(
            type_name=VertexType.STORAGE,
        )
        self.create_edge(
            type_name=EdgeType.IS_STORAGE,
            source=part,
            target=storage,
        )
        return storage

    def add_sink(self, part: Vertex) -> Vertex:
        sink: Vertex = self.create_vertex(
            type_name=VertexType.SINK,
        )
        self.create_edge(
            type_name=EdgeType.IS_SINK,
            source=part,
            target=sink,
        )
        return sink

    def add_movement(self, part: Vertex) -> Vertex:
        movement: Vertex = self.create_vertex(
            type_name=VertexType.MOVEMENT,
        )
        self.create_edge(
            type_name=EdgeType.IS_MOVEMENT,
            source=part,
            target=movement,
        )
        return movement