from src.worldgen.data import TileData, WorldData

# Hex torus: 3 outgoing directions per tile (east, north, northeast).
# Each tile also receives 3 complementary incoming edges from its neighbours.

class GridStage:
    def run(self, data: WorldData) -> WorldData:
        size: int = data.size
        tiles: dict[tuple[int, int], TileData] = {}

        for row in range(size):
            for col in range(size):
                tiles[(row, col)] = TileData(row=row, col=col)

        for (row, col), tile in tiles.items():
            for drow, dcol in [(1, 0), (0, 1), (1, 1)]:
                nrow: int = (row + drow) % size
                ncol: int = (col + dcol) % size
                tile.neighbors.append((nrow, ncol))

        data.tiles = tiles
        return data
