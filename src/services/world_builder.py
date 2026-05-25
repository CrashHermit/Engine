from arcadedb_embedded.graph import Vertex

from database.repository.location import LocationRepository

# Pointy-top hex grid, odd-r offset (1-indexed rows).
# Odd rows shift east; neighbor offsets differ by row parity.
_EVEN_ROW_OFFSETS = [(1, 0), (-1, 0), (0, 1), (-1, 1), (0, -1), (-1, -1)]
_ODD_ROW_OFFSETS  = [(1, 0), (-1, 0), (1, 1), (0, 1),  (1, -1), (0, -1)]


class WorldBuilderService:
    def __init__(self, location_repo: LocationRepository) -> None:
        self.location_repo: LocationRepository = location_repo

    def build_world(self, width: int, height: int) -> None:
        with self.location_repo.transaction():
            grid: dict[tuple[int, int], Vertex] = {}
            for row in range(1, height + 1):
                for col in range(1, width + 1):
                    coord: str = f"{col},{row}"
                    grid[(col, row)] = self.location_repo.create_location(
                        name=coord, description=coord
                    )

            for (col, row), location in grid.items():
                offsets = _ODD_ROW_OFFSETS if row % 2 == 1 else _EVEN_ROW_OFFSETS
                for dcol, drow in offsets:
                    neighbor = (col + dcol, row + drow)
                    if neighbor in grid and (col, row) < neighbor:
                        self.location_repo.connect_location(location, grid[neighbor])
