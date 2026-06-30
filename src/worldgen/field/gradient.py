import numpy as np

from src.core.model.worldgen.tile import Tile


def compute_gradient(
    tiles: dict[int, Tile],
    scalar: np.ndarray,
    descending: bool = False,
) -> np.ndarray:
    n = len(tiles)
    gradient = np.zeros((n, 3), dtype=np.float64)

    for tile in tiles.values():
        i = tile.id
        base_val = scalar[i]

        vx = 0.0
        vy = 0.0
        vz = 0.0

        for nid in tile.neighbors:
            neighbor = tiles[nid]
            delta = scalar[nid] - base_val
            if descending:
                delta = -delta

            dx = neighbor.x - tile.x
            dy = neighbor.y - tile.y
            dz = neighbor.z - tile.z

            vx += dx * delta
            vy += dy * delta
            vz += dz * delta

        dot = (vx * tile.x) + (vy * tile.y) + (vz * tile.z)

        gradient[i, 0] = vx - (dot * tile.x)
        gradient[i, 1] = vy - (dot * tile.y)
        gradient[i, 2] = vz - (dot * tile.z)

    return gradient
