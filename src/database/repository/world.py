from arcadedb_embedded.graph import Vertex
from src.core.model.database import VertexType
from src.database.repository.base import BaseRepository


class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_world(
        self,
        name: str,
        description: str,
        seed: int,
        size: int,
        biome: str,
        temperature: float,
        precipitation: float,
        elevation: float,
    ) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.WORLD,
            name=name,
            description=description,
            seed=seed,
            size=size,
            biome=biome,
            temperature=temperature,
            precipitation=precipitation,
            elevation=elevation,
        )
