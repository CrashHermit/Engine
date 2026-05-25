import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex


class HeightmapGenerator:
    def __init__(
        self,
        seed: int,
        size: int,
        major_count: int,
        major_radius_pct: int,
        detail_count: int,
        detail_radius_pct: int,
        database: arcadedb.Database,
        tiles: dict[tuple[int, int], Vertex],
    ) -> None:
        self._seed = seed
        self._size = size
        self._major_count = major_count
        self._major_radius = int(size * major_radius_pct / 100)
        self._detail_count = detail_count
        self._detail_radius = int(size * detail_radius_pct / 100)
        self._database = database
        self._tiles = tiles

    def generate(self) -> None:
        pass  # TODO: cosine falloff blob placement + normalise to 0-100
