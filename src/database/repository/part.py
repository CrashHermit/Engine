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

    def add_source(self, parts: list[Vertex]) -> Vertex:
        source: Vertex = self.create_vertex(
            type_name=VertexType.SOURCE,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_SOURCE,
                source=part,
                target=source,
            )
        return source

    def add_manipulator(self, parts: list[Vertex]) -> Vertex:
        manipulator: Vertex = self.create_vertex(
            type_name=VertexType.MANIPULATOR,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_MANIPULATOR,
                source=part,
                target=manipulator,
            )
        return manipulator

    def add_controllable(self, parts: list[Vertex]) -> Vertex:
        controllable: Vertex = self.create_vertex(
            type_name=VertexType.CONTROLLABLE,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_CONTROLLABLE,
                source=part,
                target=controllable,
            )
        return controllable

    def add_opening(self, parts: list[Vertex]) -> Vertex:
        opening: Vertex = self.create_vertex(
            type_name=VertexType.OPENING,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_OPENING,
                source=part,
                target=opening,
            )
        return opening

    def add_channel(self, parts: list[Vertex]) -> Vertex:
        channel: Vertex = self.create_vertex(
            type_name=VertexType.CHANNEL,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_CHANNEL,
                source=part,
                target=channel,
            )
        return channel

    def add_storage(self, parts: list[Vertex]) -> Vertex:
        storage: Vertex = self.create_vertex(
            type_name=VertexType.STORAGE,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_STORAGE,
                source=part,
                target=storage,
            )
        return storage

    def add_sink(self, parts: list[Vertex]) -> Vertex:
        sink: Vertex = self.create_vertex(
            type_name=VertexType.SINK,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_SINK,
                source=part,
                target=sink,
            )
        return sink

    def add_movement(self, parts: list[Vertex]) -> Vertex:
        movement: Vertex = self.create_vertex(
            type_name=VertexType.MOVEMENT,
        )
        for part in parts:
            self.create_edge(
                type_name=EdgeType.IS_MOVEMENT,
                source=part,
                target=movement,
            )
        return movement