import random
from collections import deque

import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex

from database.repository.base import BaseRepository

_HEX_DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]

# Power decay per hop keyed by cell count — mirrors FMG's getBlobPower lookup table
_BLOB_POWER: dict[int, float] = {
    1000: 0.93, 2000: 0.95, 5000: 0.97, 10000: 0.98,
    20000: 0.99, 30000: 0.991, 40000: 0.993, 50000: 0.994,
    60000: 0.995, 70000: 0.9955, 80000: 0.996, 90000: 0.9964, 100000: 0.9973,
}

_MAJOR_HEIGHT = 80.0
_DETAIL_HEIGHT = 30.0


def _blob_power(cell_count: int) -> float:
    return _BLOB_POWER.get(cell_count, 0.98)


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
        self._power = _blob_power(size * size)

    def generate(self) -> None:
        random.seed(self._seed)
        heights: dict[tuple[int, int], float] = {coord: 0.0 for coord in self._tiles}

        for _ in range(self._major_count):
            self._add_hill(heights, h=_MAJOR_HEIGHT, radius=self._major_radius)
        for _ in range(self._detail_count):
            self._add_hill(heights, h=_DETAIL_HEIGHT, radius=self._detail_radius)

        self._normalise(heights)
        self._save(heights)

    def _add_hill(
        self, heights: dict[tuple[int, int], float], h: float, radius: int
    ) -> None:
        size = self._size

        # pick center; skip tiles already near the height cap (mirrors FMG retry logic)
        cq, cr = random.randrange(size), random.randrange(size)
        for _ in range(50):
            if heights[(cq, cr)] + h <= 90:
                break
            cq, cr = random.randrange(size), random.randrange(size)

        change: dict[tuple[int, int], float] = {(cq, cr): h}
        dist: dict[tuple[int, int], int] = {(cq, cr): 0}
        queue: deque[tuple[int, int]] = deque([(cq, cr)])

        while queue:
            q, r = queue.popleft()
            current = change[(q, r)]
            d = dist[(q, r)]

            if d >= radius:
                continue

            for dq, dr in _HEX_DIRECTIONS:
                nb = ((q + dq) % size, (r + dr) % size)
                if nb in change:
                    continue

                # FMG: change[neighbor] = change[parent] ** blobPower * noise
                nb_change = current ** self._power * random.uniform(0.9, 1.1)
                if nb_change <= 1:
                    continue

                change[nb] = nb_change
                dist[nb] = d + 1
                queue.append(nb)

        for coord, delta in change.items():
            heights[coord] = min(heights[coord] + delta, 100.0)

    def _normalise(self, heights: dict[tuple[int, int], float]) -> None:
        max_h = max(heights.values())
        if max_h == 0:
            return
        for coord in heights:
            heights[coord] = round(heights[coord] / max_h * 100)

    def _save(self, heights: dict[tuple[int, int], float]) -> None:
        repo = BaseRepository(self._database)
        with repo.transaction():
            for coord, h in heights.items():
                repo.update_vertex(self._tiles[coord], height=int(h))
