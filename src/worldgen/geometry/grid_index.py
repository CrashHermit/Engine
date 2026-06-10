from __future__ import annotations

from src.worldgen.model import GridTile, WorldData


class GridIndex:
    def __init__(self, size: int) -> None:
        self._size: int = size

    def build_base_grid(self, world_data: WorldData) -> None:
        for x in range(self._size):
            for y in range(self._size):
                world_data.grid.append(GridTile(x=x, y=y))
