from worldgen.data import TileData, WorldData

# Hex torus: 3 outgoing directions per tile (east, north, northeast).
# Each tile also receives 3 complementary incoming edges from its neighbours.
_OUTGOING_DIRECTIONS = [(1, 0), (0, 1), (1, 1)]


class GridStage:
    def run(self, data: WorldData) -> WorldData:
        size = data.size
        tiles: dict[tuple[int, int], TileData] = {}

        for q in range(size):
            for r in range(size):
                tiles[(q, r)] = TileData(q=q, r=r)

        for (q, r), tile in tiles.items():
            for dq, dr in _OUTGOING_DIRECTIONS:
                nq = (q + dq) % size
                nr = (r + dr) % size
                tile.neighbors.append((nq, nr))

        data.tiles = tiles
        return data
