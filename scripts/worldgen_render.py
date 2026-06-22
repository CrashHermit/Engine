from __future__ import annotations

import colorsys
import math
from typing import TypeAlias
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile
from src.worldgen.context import WorldContext
from src.worldgen.fields import GridFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.types import Float64Array, Int32Array


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
    insolation: Float64Array  # mesh-side intermediate, baked per-tile for display only


class Layer(StrEnum):
    ELEVATION = "elevation"
    LAND = "land"
    MESH = "mesh"
    PLATES = "plates"
    UPLIFT = "uplift"
    DRAINAGE = "drainage"
    INSOLATION = "insolation"
    TEMPERATURE = "temperature"
    WIND = "wind"
    PRECIPITATION = "precipitation"
    DISCHARGE = "discharge"
    SAVAGERY = "savagery"
    MAGIC_STRENGTH = "magic_strength"
    MAGIC_VALENCE = "magic_valence"
    MAGIC_CHANNELS = "magic_channels"
    BIOMES = "biomes"

LAYER_ORDER: tuple[Layer, ...] = (
    Layer.ELEVATION,
    Layer.LAND,
    Layer.MESH,
    Layer.PLATES,
    Layer.UPLIFT,
    Layer.DRAINAGE,
    Layer.INSOLATION,
    Layer.TEMPERATURE,
    Layer.WIND,
    Layer.PRECIPITATION,
    Layer.DISCHARGE,
    Layer.SAVAGERY,
    Layer.MAGIC_STRENGTH,
    Layer.MAGIC_VALENCE,
    Layer.MAGIC_CHANNELS,
    Layer.BIOMES,
)

LAYER_LABELS: dict[Layer, str] = {
    Layer.ELEVATION: "Elevation",
    Layer.LAND: "Land",
    Layer.MESH: "Mesh debug",
    Layer.PLATES: "Plates",
    Layer.UPLIFT: "Uplift",
    Layer.DRAINAGE: "Drainage",
    Layer.INSOLATION: "Insolation",
    Layer.TEMPERATURE: "Temperature",
    Layer.WIND: "Wind",
    Layer.PRECIPITATION: "Precipitation",
    Layer.DISCHARGE: "Discharge",
    Layer.SAVAGERY: "Savagery",
    Layer.MAGIC_STRENGTH: "Magic strength",
    Layer.MAGIC_VALENCE: "Magic valence",
    Layer.MAGIC_CHANNELS: "Magic channels",
    Layer.BIOMES: "Biomes",
}

LAYER_DESCRIPTIONS: dict[Layer, str] = {
    Layer.ELEVATION: "Terrain height. Dark blue = ocean, green = low land, tan = high land.",
    Layer.LAND: "Land vs ocean.",
    Layer.MESH: "Debug: each color is a Voronoi cell id (verify periodic sampling).",
    Layer.PLATES: "Tectonic plates; each color is a plate id (ragged Voronoi partition).",
    Layer.UPLIFT: "Base tectonic uplift before boundary belts. Bright = continental plates, dark = oceanic.",
    Layer.DRAINAGE: "Upstream drainage area per cell (log). Brighter = more flow. River valleys visible as bright veins.",
    Layer.INSOLATION: "Authored energy field. Bright = hot sunband, dark = cold frostbelt; wraps seamlessly.",
    Layer.TEMPERATURE: "Warmth [0,1]. Cold frostbelt and mountain peaks blue; hot sunband red; mild coasts.",
    Layer.WIND: "Wind: hue = direction (atan2 v,u), brightness = speed. Belts deflect around ranges.",
    Layer.PRECIPITATION: "Rainfall [0,1]. Wet windward coasts bright; dry interiors and rain shadows dark.",
    Layer.DISCHARGE: "Rain-weighted water flow (log). Brighter = more water. River valleys glow brighter in wet regions.",
    Layer.SAVAGERY: "Legible danger [0,1]. Bright deep interiors, deserts, frostbelt, and ranges; calm temperate coasts.",
    Layer.MAGIC_STRENGTH: "Leyline intensity [0,1]. Bright web of lines between nexuses; dim floor elsewhere.",
    Layer.MAGIC_VALENCE: "Magic valence [-1,1]. Diverging palette: corrupt (magenta) vs pure (cyan); neutral grey off the web.",
    Layer.MAGIC_CHANNELS: "Channel composition (corpus/mens/anima) mapped straight to RGB.",
    Layer.BIOMES: "Dominant biome per tile (argmax of the soft weights); one hue per biome.",
}


def generate_world(size: int, seed: int) -> Phase0World:
    """Run the Phase 0 pipeline and bake mesh fields onto the gameplay grid."""
    ctx: WorldContext = WorldgenPipeline().run(seed=seed, size=size)
    nearest: Int32Array = nearest_cell_per_tile(
        geometry=ctx.geometry,
        size=ctx.config.size,
    )
    grid: GridFields = bake_to_grid(fields=ctx.fields, nearest=nearest)

    # insolation stays off the product grid (mesh-side intermediate); bake it
    # per-tile here purely so the viewer can show the authored energy field.
    insolation_field: Float64Array | None = ctx.fields.insolation
    insolation: Float64Array = (
        insolation_field[nearest]
        if insolation_field is not None
        else np.zeros(nearest.shape[0], dtype=float)
    )

    return Phase0World(
        seed=seed,
        size=size,
        grid=grid,
        geometry=ctx.geometry,
        nearest=nearest,
        insolation=insolation,
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

    if layer == Layer.DRAINAGE:
        d: float = float(grid.drainage[tile_index])
        if d <= 0.0 or not grid.is_land[tile_index]:
            return (10, 20, 30)  # dark background for ocean / sinks
        # log scale: drainage spans 1 to thousands
        log_d: float = math.log(d) / math.log(1000.0)  # normalize so d=1000 -> 1
        t: float = max(0.0, min(1.0, log_d))
        return _lerp_color(low=(30, 60, 100), high=(255, 240, 200), t=t)

    if layer == Layer.INSOLATION:
        t: float = max(0.0, min(1.0, float(world.insolation[tile_index])))
        return _lerp_color(low=(20, 30, 90), high=(255, 240, 180), t=t)

    if layer == Layer.TEMPERATURE:
        t: float = max(0.0, min(1.0, float(grid.temperature[tile_index])))
        # cold = blue, mild = pale, hot = red
        return _lerp_color(low=(40, 80, 200), high=(220, 60, 50), t=t)

    if layer == Layer.PRECIPITATION:
        t: float = max(0.0, min(1.0, float(grid.precipitation[tile_index])))
        # dry = tan, wet = deep green-blue
        return _lerp_color(low=(200, 180, 120), high=(20, 90, 130), t=t)

    if layer == Layer.WIND:
        wind_u: float = float(grid.wind_u[tile_index])
        wind_v: float = float(grid.wind_v[tile_index])
        mag: float = max(0.0, min(1.0, float(grid.wind_magnitude[tile_index])))
        hue: float = (math.atan2(wind_v, wind_u) / (2.0 * math.pi)) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(h=hue, s=0.8, v=0.2 + 0.8 * mag)
        return int(red * 255), int(green * 255), int(blue * 255)

    if layer == Layer.DISCHARGE:
        d: float = float(grid.discharge[tile_index])
        if d <= 0.0 or not grid.is_land[tile_index]:
            return (10, 20, 30)  # dark background for ocean / sinks
        # log scale: discharge spans small to very large values
        log_d: float = math.log(d) / math.log(10000.0)  # normalize so d=10000 -> 1
        t: float = max(0.0, min(1.0, log_d))
        return _lerp_color(low=(30, 60, 120), high=(100, 200, 255), t=t)

    if layer == Layer.SAVAGERY:
        t: float = max(0.0, min(1.0, float(grid.savagery[tile_index])))
        # calm green -> dangerous crimson
        return _lerp_color(low=(40, 90, 60), high=(200, 40, 40), t=t)

    if layer == Layer.MAGIC_STRENGTH:
        t: float = max(0.0, min(1.0, float(grid.magic_strength[tile_index])))
        return _lerp_color(low=(15, 15, 30), high=(180, 120, 255), t=t)

    if layer == Layer.MAGIC_VALENCE:
        v: float = max(-1.0, min(1.0, float(grid.magic_valence[tile_index])))
        # corrupt (-1) = magenta, neutral (0) = grey, pure (+1) = cyan
        if v < 0.0:
            return _lerp_color(low=(120, 120, 120), high=(210, 40, 160), t=-v)
        return _lerp_color(low=(120, 120, 120), high=(40, 200, 210), t=v)

    if layer == Layer.MAGIC_CHANNELS:
        channels = grid.magic_channels[tile_index]
        # corpus/mens/anima -> RGB; scale so the dominant channel is vivid
        peak: float = max(float(channels.max()), 1e-6)
        return (
            int(255 * float(channels[0]) / peak),
            int(255 * float(channels[1]) / peak),
            int(255 * float(channels[2]) / peak),
        )

    if layer == Layer.BIOMES:
        if not grid.is_land[tile_index]:
            return WATER_COLOR
        biome_col: int = int(np.argmax(grid.biome_weights[tile_index]))
        hue: float = (biome_col * 0.6180339887) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(h=hue, s=0.55, v=0.9)
        return int(red * 255), int(green * 255), int(blue * 255)

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
