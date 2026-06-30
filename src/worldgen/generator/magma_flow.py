import numpy as np

from core.model.worldgen.tile import Tile
from worldgen.scalar.noise import generate_3d_fbm


class MagmaFlow:
    def __init__(self, tiles: Tile) -> None:
        self.tiles = tiles

    def _generate_magma_flow_fbm(self) -> np.ndarray:
        pass
