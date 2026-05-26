from src.worldgen.data import TileData, WorldData

# Hex torus: 3 outgoing directions per tile (east, north, northeast).
# Each tile also receives 3 complementary incoming edges from its neighbours.

class GridStage:
    def run(self, data: WorldData) -> WorldData:
        size: int = data.size
        tiles: dict[tuple[int, int], TileData] = {}

        for q in range(size):
            for r in range(size):
                tiles[(q, r)] = TileData(q=q, r=r)

        for (q, r), tile in tiles.items():
            for dq, dr in [(1, 0), (0, 1), (1, 1)]:
                nq: int = (q + dq) % size
                nr: int = (r + dr) % size
                tile.neighbors.append((nq, nr))

        data.tiles = tiles
        return data
