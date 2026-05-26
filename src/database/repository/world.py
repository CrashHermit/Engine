from arcadedb_embedded.graph import Vertex

from core.model.database import VertexType
from database.repository.base import BaseRepository


class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

    def create_world(
        self,
        name: str,
        description: str,
        seed: int,
        size: int,
        major_count: int,
        major_radius_pct: int,
        detail_count: int,
        detail_radius_pct: int,
    ) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.WORLD,
            name=name,
            description=description,
            seed=seed,
            size=size,
            major_count=major_count,
            major_radius_pct=major_radius_pct,
            detail_count=detail_count,
            detail_radius_pct=detail_radius_pct,
        )
