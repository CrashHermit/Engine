from __future__ import annotations

import colorsys
from typing import TypeAlias
from dataclasses import dataclass
from enum import StrEnum

from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile
from src.worldgen.context import WorldContext
from src.worldgen.fields import GridFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.types import Int32Array


RGB: TypeAlias = tuple[int, int, int]

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
    PLATES = "plates"
    UPLIFT = "uplift"

LAYER_ORDER: tuple[Layer, ...] = (
    Layer.ELEVATION,
    Layer.LAND,
    Layer.MESH,
    Layer.PLATES,
    Layer.UPLIFT,
)

LAYER_LABELS: dict[Layer, str] = {
    Layer.ELEVATION: "Elevation",
    Layer.LAND: "Land",
    Layer.MESH: "Mesh debug",
    Layer.PLATES: "Plates",
    Layer.UPLIFT: "Uplift",
}

LAYER_DESCRIPTIONS: dict[Layer, str] = {
    Layer.ELEVATION: "Terrain height. Dark blue = ocean, green = low land, tan = high land.",
    Layer.LAND: "Land vs ocean.",
    Layer.MESH: "Debug: each color is a Voronoi cell id (verify periodic sampling).",
    Layer.PLATES: "Tectonic plates; each color is a plate id (ragged Voronoi partition).",
    Layer.UPLIFT: "Base tectonic uplift before boundary belts. Bright = continental plates, dark = oceanic."
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
    grid: GridFields = world.grid

    if not grid.is_land[tile_index]:
        if layer in {Layer.ELEVATION, Layer.LAND}:
            return WATER_COLOR

    if layer == Layer.LAND:
        return LAND_COLOR

    if layer == Layer.ELEVATION:
        t: float = (float(grid.elevation[tile_index]) - z_min) / z_span
        return _lerp_color(low=LAND_COLOR, high=(220, 210, 180), t=t)

    if layer == Layer.PLATES:
        plate_id: int = int(grid.plate_id[tile_index])
        hue: float = (plate_id * 0.6180339887) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(h=hue, s=0.7, v=0.9)
        return int(red * 255), int(green * 255), int(blue * 255)

    if layer == Layer.MESH:
        cell_id: int = int(world.nearest[tile_index])
        hue: float = (cell_id * 0.6180339887) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(h=hue, s=0.7, v=0.9)
        return int(red * 255), int(green * 255), int(blue * 255)

    if layer == Layer.UPLIFT:
        u: float = float(grid.uplift[tile_index])
        # continental_uplift defaults to 1.0, oceanic to 0.0
        t: float = max(0.0, min(1.0, u))
        return _lerp_color(low=(30, 40, 80), high=(220, 200, 160), t=t)

    return (0, 0, 0)


def rasterize(world: Phase0World, layer: Layer) -> dict[RGB, list[tuple[int, int]]]:
    """Group canvas pixels by color for sparse canvas updates."""
    return rasterize_display(world=world, layer=layer, display_size=world.size)


def rasterize_display(
    world: Phase0World,
    layer: Layer,
    display_size: int,
) -> dict[RGB, list[tuple[int, int]]]:
    """Rasterize a layer onto a display_size x display_size canvas.

    Downsamples when display_size < world.size (zoom out) and upsamples with
    nearest-neighbour when display_size > world.size (zoom in).
    """
    world_size: int = world.size
    display_size = max(1, min(display_size, world_size * 8))
    grid: GridFields = world.grid
    pixels: dict[RGB, list[tuple[int, int]]] = {}
    z_min: float = float(grid.elevation.min())
    z_max: float = float(grid.elevation.max())
    z_span: float = z_max - z_min if z_max > z_min else 1.0

    display_y: int
    display_x: int
    for display_y in range(display_size):
        for display_x in range(display_size):
            tile_x: int = display_x * world_size // display_size
            tile_y: int = display_y * world_size // display_size
            tile_index: int = _tile_index(x=tile_x, y=tile_y, size=world_size)
            color: RGB = _tile_color(
                world=world,
                layer=layer,
                tile_index=tile_index,
                z_min=z_min,
                z_span=z_span,
            )
            pixels.setdefault(color, []).append((display_x, display_y))

    return pixels


def rasterize_grid(world: Phase0World, layer: Layer) -> list[list[RGB]]:
    """Dense size x size color grid (row-major by y then x)."""
    size = world.size
    grid = [[(0, 0, 0) for _ in range(size)] for _ in range(size)]
    for color, coords in rasterize(world, layer).items():
        for x, y in coords:
            grid[y][x] = color
    return grid
