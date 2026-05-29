from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.model.database import EdgeType, VertexType
from src.core.model.part import Shape, Status, SizeScale
from src.database.repository.base import BaseRepository

if TYPE_CHECKING:
    from arcadedb_embedded.graph import Vertex


class PartRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

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
        part: Vertex = self._base.create_vertex(
            type_name=VertexType.PART,
            name=name,
            length=length,
            width=width,
            height=height,
            shape=shape,
            status=status,
            description=description,
        )
        self._base.create_edge(type_name=EdgeType.HAS_PART, source=character, target=part)
        return part

    def attach(self, source: Vertex, target: Vertex) -> None:
        self._base.create_edge(type_name=EdgeType.ATTACHED_TO, source=source, target=target)

    ############################################################################
    # Reads + persistent harm (decision #19) — wound boxes stored on the PART
    ############################################################################

    def list_parts(self, character: Vertex) -> list[Vertex]:
        return [edge.get_in() for edge in character.get_out_edges(EdgeType.HAS_PART)]

    def get_part(self, character: Vertex, name: str) -> Vertex | None:
        for part in self.list_parts(character):
            if part.get(name="name") == name:
                return part
        return None

    def attached_parts(self, part: Vertex) -> list[Vertex]:
        """Parts attached beyond this one, toward the extremities (the distal side)."""
        return [edge.get_in() for edge in part.get_out_edges(EdgeType.ATTACHED_TO)]

    def get_wound_boxes(self, part: Vertex) -> int:
        return part.get(name="wound_boxes") or 0

    def get_capacity(self, part: Vertex, default: int) -> int:
        return part.get(name="wound_capacity") or default

    def set_wound_state(self, part: Vertex, *, filled: int, status: str) -> None:
        self._base.update_vertex(vertex=part, wound_boxes=filled, status=status)

    def remove_part(self, part: Vertex) -> None:
        """Delete a part vertex (DESTROYED parts are severed from the body)."""
        self._base.delete_vertex(part)

    def add_source(self, part: Vertex) -> Vertex:
        source = self._base.create_vertex(type_name=VertexType.SOURCE)
        self._base.create_edge(type_name=EdgeType.IS_SOURCE, source=part, target=source)
        return source

    def add_manipulator(self, part: Vertex) -> Vertex:
        manipulator = self._base.create_vertex(type_name=VertexType.MANIPULATOR)
        self._base.create_edge(type_name=EdgeType.IS_MANIPULATOR, source=part, target=manipulator)
        return manipulator

    def add_controllable(self, part: Vertex) -> Vertex:
        controllable = self._base.create_vertex(type_name=VertexType.CONTROLLABLE)
        self._base.create_edge(type_name=EdgeType.IS_CONTROLLABLE, source=part, target=controllable)
        return controllable

    def add_opening(self, part: Vertex) -> Vertex:
        opening = self._base.create_vertex(type_name=VertexType.OPENING)
        self._base.create_edge(type_name=EdgeType.IS_OPENING, source=part, target=opening)
        return opening

    def add_channel(self, part: Vertex) -> Vertex:
        channel = self._base.create_vertex(type_name=VertexType.CHANNEL)
        self._base.create_edge(type_name=EdgeType.IS_CHANNEL, source=part, target=channel)
        return channel

    def add_storage(self, part: Vertex) -> Vertex:
        storage = self._base.create_vertex(type_name=VertexType.STORAGE)
        self._base.create_edge(type_name=EdgeType.IS_STORAGE, source=part, target=storage)
        return storage

    def add_sink(self, part: Vertex) -> Vertex:
        sink = self._base.create_vertex(type_name=VertexType.SINK)
        self._base.create_edge(type_name=EdgeType.IS_SINK, source=part, target=sink)
        return sink

    def add_movement(self, part: Vertex) -> Vertex:
        movement = self._base.create_vertex(type_name=VertexType.MOVEMENT)
        self._base.create_edge(type_name=EdgeType.IS_MOVEMENT, source=part, target=movement)
        return movement
