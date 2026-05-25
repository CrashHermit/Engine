from arcadedb_embedded.graph import Vertex
from core.model.part import Shape, Status, SizeScale
from database.repository.part import PartRepository


class PartService:
    def __init__(self, part_repo: PartRepository) -> None:
        self.part_repo: PartRepository = part_repo

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

    def attach(self, source: Vertex, target: Vertex) -> None:
        with self.part_repo.transaction():
            self.part_repo.attach(source=source, target=target)
