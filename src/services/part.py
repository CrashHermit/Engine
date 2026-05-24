from arcadedb_embedded.graph import Vertex
from core.model.part import Shape, Status, SizeScale, PartFunction
from database.repository.part import PartRepository


class PartService:
    def __init__(self, part_repo: PartRepository) -> None:
        self.part_repo: PartRepository = part_repo

    def add_core_part(
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
        with self.part_repo.transaction():
            return self.part_repo.add_core_part(
                character=character,
                name=name,
                length=length,
                width=width,
                height=height,
                shape=shape,
                status=status,
                description=description,
            )

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
        with self.part_repo.transaction():
            return self.part_repo.add_part(
                character=character,
                name=name,
                length=length,
                width=width,
                height=height,
                shape=shape,
                status=status,
                description=description,
            )

    def add_function(self, part: Vertex, function: PartFunction) -> Vertex:
        with self.part_repo.transaction():
            return self.part_repo.add_function(part=part, function=function)
