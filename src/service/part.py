from arcadedb_embedded.graph import Vertex

from src.core.model.part import Shape, SizeScale, Status
from src.database.repository.base import BaseRepository
from src.database.repository.part import PartRepository


class PartService:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base
        self._part_repo: PartRepository = PartRepository(base=base)

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
        with self._base.transaction():
            return self._part_repo.add_part(
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
        with self._base.transaction():
            self._part_repo.attach(source=source, target=target)
