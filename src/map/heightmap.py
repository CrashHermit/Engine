from opensimplex import OpenSimplex

from map.config import HeightmapConfig
from map.grid import TileData


def generate_heightmap(
    tiles: list[TileData],
    rows: int,
    cols: int,
    config: HeightmapConfig,
) -> dict[tuple[int, int], int]:
    """
    Return elevation (0–100) for every tile using fractal Brownian motion.

    Tiles with elevation < config.sea_level are ocean; the rest are land.
    The noise is sampled on a torus so the grid wraps without seams.
    """
    gen = OpenSimplex(config.seed)
    elevations: dict[tuple[int, int], int] = {}

    for tile in tiles:
        # Map (row, col) onto the surface of a torus so edges wrap seamlessly.
        # Two sine/cosine pairs encode row and col each as a circle in 4D space.
        angle_x = (tile.col / cols) * 2 * 3.141592653589793
        angle_y = (tile.row / rows) * 2 * 3.141592653589793
        tx, ty = _cos(angle_x), _sin(angle_x)
        tz, tw = _cos(angle_y), _sin(angle_y)

        value = 0.0
        amplitude = 1.0
        frequency = config.scale
        max_value = 0.0

        for _ in range(config.octaves):
            value += gen.noise4(tx * frequency, ty * frequency, tz * frequency, tw * frequency) * amplitude
            max_value += amplitude
            amplitude *= config.persistence
            frequency *= config.lacunarity

        # Normalise from [-max_value, max_value] → [0, 100]
        normalised = (value / max_value + 1.0) / 2.0
        elevations[(tile.row, tile.col)] = int(normalised * 100)

    return elevations


def _cos(x: float) -> float:
    import math
    return math.cos(x)


def _sin(x: float) -> float:
    import math
    return math.sin(x)
