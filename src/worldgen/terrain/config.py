"""Coarse spherical coastal elevation settings."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TerrainConfig:
    """Widths as percentages of circumference; heights as percentages of radius."""

    inland_width_percent: float = 2.0
    shelf_width_percent: float = 1.25
    slope_width_percent: float = 1.25
    interior_height_percent: float = 0.00942
    shelf_depth_percent: float = 0.00314
    basin_depth_percent: float = 0.07063
