from __future__ import annotations

from src.worldgen.data import GridPositionData, GridTileData, WorldData


class GridIndex:
    def __init__(self, size: int) -> None:
        self._size: int = size

    def tile_key(self, position: GridPositionData) -> tuple[int, int]:
        return (position.x, position.y)

    def build_tile_index(
        self, grid: list[GridTileData]
    ) -> dict[tuple[int, int], GridTileData]:
        return {self.tile_key(tile.position): tile for tile in grid}

    def build_base_grid(self, world_data: WorldData) -> WorldData:
        for x in range(self._size):
            for y in range(self._size):
                world_data.grid.append(
                    GridTileData(position=GridPositionData(x=x, y=y))
                )
        return world_data

    def build_neighbors(self, world_data: WorldData) -> WorldData:
        for tile in world_data.grid:
            neighbors: list[GridPositionData] = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    wrap_x: int = (tile.position.x + dx) % self._size
                    wrap_y: int = (tile.position.y + dy) % self._size

                    neighbor_index: int = wrap_x * self._size + wrap_y
                    neighbors.append(world_data.grid[neighbor_index].position)

            tile.neighbors = neighbors
        return world_data
