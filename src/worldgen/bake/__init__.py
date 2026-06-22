"""Grid rasterization: mesh → tiles, then river stamping on top."""

from src.worldgen.bake.grid import bake_and_stamp, bake_to_grid, nearest_cell_per_tile
from src.worldgen.bake.rivers import stamp_rivers

__all__ = ["nearest_cell_per_tile", "bake_to_grid", "stamp_rivers", "bake_and_stamp"]
