from __future__ import annotations

import colorsys
from dataclasses import dataclass
from enum import StrEnum

from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile
from src.worldgen.context import WorldContext
from src.worldgen.fields import GridFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.types import Int32Array

RGB = tuple[int, int, int]

WATER_COLOR: RGB = (20, 60, 140)
LAND_COLOR: RGB = (30, 80, 40)
GRID_COLOR: RGB = (40, 40, 50)


@dataclass
class Phase0World:
    """Everything the Phase 0 viewer needs."""

    seed: int
    size: int
    grid: GridFields
    geometry: MeshGeometry
    nearest: Int32Array


class Layer(StrEnum):
    ELEVATION = "elevation"
    LAND = "land"
    MESH = "mesh"


LAYER_ORDER: tuple[Layer, ...] = (
    Layer.ELEVATION,
    Layer.LAND,
    Layer.MESH,
)

LAYER_LABELS: dict[Layer, str] = {
    Layer.ELEVATION: "Elevation",
    Layer.LAND: "Land",
    Layer.MESH: "Mesh debug",
}

LAYER_DESCRIPTIONS: dict[Layer, str] = {
    Layer.ELEVATION: (
        "Terrain height. Dark blue = ocean, green = low land, tan = high land."
    ),
    Layer.LAND: "Land vs ocean.",
    Layer.MESH: "Debug: each color is a Voronoi cell id (verify periodic sampling).",
}


def generate_world(size: int, seed: int) -> Phase0World:
    """Run the Phase 0 pipeline and bake mesh fields onto the gameplay grid."""
    ctx: WorldContext = WorldgenPipeline().run(seed=seed, size=size)
    nearest: Int32Array = nearest_cell_per_tile(
        geometry=ctx.geometry,
        size=ctx.config.size,
    )
    grid: GridFields = bake_to_grid(fields=ctx.fields, nearest=nearest)
    return Phase0World(
        seed=seed,
        size=size,
        grid=grid,
        geometry=ctx.geometry,
        nearest=nearest,
    )


def _lerp_color(low: RGB, high: RGB, t: float) -> RGB:
    """Blend two RGB colors by t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    return (
        int(low[0] + (high[0] - low[0]) * t),
        int(low[1] + (high[1] - low[1]) * t),
        int(low[2] + (high[2] - low[2]) * t),
    )


def _tile_index(x: int, y: int, size: int) -> int:
    """Flat tile id matching bake meshgrid indexing='ij'."""
    return x * size + y


def _tile_color(
    world: Phase0World,
    layer: Layer,
    tile_index: int,
    z_min: float,
    z_span: float,
) -> RGB:
    """Map one baked grid tile to an RGB color for the requested layer."""
    grid = world.grid

    if not grid.is_land[tile_index]:
        if layer in {Layer.ELEVATION, Layer.LAND}:
            return WATER_COLOR

    if layer == Layer.LAND:
        return LAND_COLOR

    if layer == Layer.ELEVATION:
        t = (float(grid.elevation[tile_index]) - z_min) / z_span
        return _lerp_color(LAND_COLOR, (220, 210, 180), t)

    if layer == Layer.MESH:
        cell_id = int(world.nearest[tile_index])
        hue = (cell_id * 0.6180339887) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
        return int(red * 255), int(green * 255), int(blue * 255)

    return (0, 0, 0)


def rasterize(world: Phase0World, layer: Layer) -> dict[RGB, list[tuple[int, int]]]:
    """Group canvas pixels by color for sparse canvas updates."""
    size = world.size
    grid = world.grid
    pixels: dict[RGB, list[tuple[int, int]]] = {}
    z_min = float(grid.elevation.min())
    z_max = float(grid.elevation.max())
    z_span = z_max - z_min if z_max > z_min else 1.0

    y: int
    x: int
    for y in range(size):
        for x in range(size):
            tile_index = _tile_index(x, y, size)
            color = _tile_color(world, layer, tile_index, z_min, z_span)
            pixels.setdefault(color, []).append((x, y))

    return pixels


def rasterize_grid(world: Phase0World, layer: Layer) -> list[list[RGB]]:
    """Dense size x size color grid (row-major by y then x)."""
    size = world.size
    grid = [[(0, 0, 0) for _ in range(size)] for _ in range(size)]
    for color, coords in rasterize(world, layer).items():
        for x, y in coords:
            grid[y][x] = color
    return grid
