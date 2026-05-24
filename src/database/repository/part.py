import uuid
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType, EdgeType
from core.model.part import Shape, Status, SizeScale, PartFunction
from database.repository.character import CharacterRepository


_FUNCTION_MAP: dict[PartFunction, tuple[VertexType, EdgeType]] = {
    PartFunction.SOURCE: (VertexType.SOURCE, EdgeType.IS_SOURCE),
    PartFunction.SINK: (VertexType.SINK, EdgeType.IS_SINK),
    PartFunction.STORAGE: (VertexType.STORAGE, EdgeType.IS_STORAGE),
    PartFunction.MANIPULATOR: (VertexType.MANIPULATOR, EdgeType.IS_MANIPULATOR),
    PartFunction.MOVEMENT: (VertexType.MOVEMENT, EdgeType.IS_MOVEMENT),
    PartFunction.OPENING: (VertexType.OPENING, EdgeType.IS_OPENING),
    PartFunction.CHANNEL: (VertexType.CHANNEL, EdgeType.IS_CHANNEL),
    PartFunction.CONTROLLABLE: (VertexType.CONTROLLABLE, EdgeType.IS_CONTROLLABLE),
}


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
            id=str(uuid.uuid4()),
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

    def add_function(self, part: Vertex, function: PartFunction) -> Vertex:
        vertex_type, edge_type = _FUNCTION_MAP[function]
        node: Vertex = self.create_vertex(
            type_name=vertex_type,
            id=str(uuid.uuid4()),
        )
        self.create_edge(
            type_name=edge_type,
            source=part,
            target=node,
        )
        return node
