from __future__ import annotations

import colorsys
from enum import StrEnum

from src.core.model.environment.ecology.biome import BiomeEnum
from src.worldgen.data import GridTileData, WorldData
from src.worldgen.geometry.mesh_index import VoronoiMeshIndex
from src.worldgen.pipeline import WorldgenPipeline

RGB = tuple[int, int, int]

WATER_COLOR: RGB = (20, 60, 140)
LAKE_COLOR: RGB = (50, 120, 200)
RIVER_COLOR: RGB = (80, 200, 255)
GRID_COLOR: RGB = (40, 40, 50)


class Layer(StrEnum):
    ELEVATION = "elevation"
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    SAVAGERY = "savagery"
    ALIGNMENT = "alignment"
    BIOMES = "biomes"
    HYDROLOGY = "hydrology"
    RIVERS = "rivers"
    LANDMASSES = "landmasses"
    MESH = "mesh"


LAYER_ORDER: tuple[Layer, ...] = (
    Layer.ELEVATION,
    Layer.TEMPERATURE,
    Layer.PRECIPITATION,
    Layer.SAVAGERY,
    Layer.ALIGNMENT,
    Layer.BIOMES,
    Layer.HYDROLOGY,
    Layer.RIVERS,
    Layer.LANDMASSES,
    Layer.MESH,
)

LAYER_LABELS: dict[Layer, str] = {
    Layer.ELEVATION: "Elevation",
    Layer.TEMPERATURE: "Temperature",
    Layer.PRECIPITATION: "Precipitation",
    Layer.SAVAGERY: "Savagery",
    Layer.ALIGNMENT: "Alignment",
    Layer.BIOMES: "Biomes",
    Layer.HYDROLOGY: "Hydrology",
    Layer.RIVERS: "Rivers",
    Layer.LANDMASSES: "Landmasses",
    Layer.MESH: "Mesh debug",
}

LAYER_DESCRIPTIONS: dict[Layer, str] = {
    Layer.ELEVATION: (
        "Terrain height. Dark blue = ocean, light blue = lakes, "
        "green = low land, tan = high land."
    ),
    Layer.TEMPERATURE: (
        "Surface warmth. Blue = cold, green = mild, yellow = warm, red = hot."
    ),
    Layer.PRECIPITATION: "Moisture. Tan = dry, blue = wet.",
    Layer.SAVAGERY: "Low = tame, high = savage.",
    Layer.ALIGNMENT: "Negative = dark/chaotic, positive = ordered/holy.",
    Layer.BIOMES: (
        "Dominant biome per land tile. Each hue is a biome; water stays blue."
    ),
    Layer.HYDROLOGY: (
        "Water flow. Dark blue = ocean, light blue = lakes, "
        "tan-to-blue = drainage on land."
    ),
    Layer.RIVERS: (
        "Elevation base with rivers highlighted in cyan from mesh flux routing."
    ),
    Layer.LANDMASSES: (
        "Connected land components: hue = landmass id, saturation = size class "
        "(bright=major, medium=landmass, muted=island)."
    ),
    Layer.MESH: "Debug: each color is a Voronoi cell id (verify periodic sampling).",
}


def generate_world(size: int, seed: int) -> WorldData:
    return WorldgenPipeline().run(WorldData(size=size, seed=seed))


def _lerp_color(low: RGB, high: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return (
        int(low[0] + (high[0] - low[0]) * t),
        int(low[1] + (high[1] - low[1]) * t),
        int(low[2] + (high[2] - low[2]) * t),
    )


def _thermal_color(t: float) -> RGB:
    hue = (1.0 - max(0.0, min(1.0, t))) * 0.66
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.9, 0.95)
    return int(red * 255), int(green * 255), int(blue * 255)


def _biome_color(biome: BiomeEnum) -> RGB:
    hue = (hash(biome.value) % 360) / 360.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.65, 0.85)
    return int(red * 255), int(green * 255), int(blue * 255)


def _scalar_range(grid: list[GridTileData], accessor) -> tuple[float, float]:
    values = [accessor(tile) for tile in grid]
    if not values:
        return (0.0, 1.0)
    low = min(values)
    high = max(values)
    if low == high:
        return (low, low + 1.0)
    return low, high


def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return (value - low) / (high - low)


def _water_color(tile: GridTileData) -> RGB | None:
    if not tile.position.is_land:
        return WATER_COLOR
    if tile.position.is_lake:
        return LAKE_COLOR
    return None


def _dominant_biome(tile: GridTileData) -> BiomeEnum | None:
    if not tile.position.biome_weights:
        return None
    return max(tile.position.biome_weights, key=lambda entry: entry.weight).biome


def tile_color(
    tile: GridTileData,
    layer: Layer,
    ranges: dict[str, tuple[float, float]],
    world_data: WorldData,
    mesh_index: VoronoiMeshIndex | None = None,
) -> RGB:
    position = tile.position
    water = _water_color(tile)

    if layer in {Layer.ELEVATION, Layer.BIOMES} and water is not None:
        return water

    if layer == Layer.ELEVATION:
        low, high = ranges["elevation"]
        t = _normalize(position.z, low, high)
        return _lerp_color((30, 80, 40), (220, 210, 180), t)

    if layer == Layer.TEMPERATURE:
        low, high = ranges["temperature"]
        t = _normalize(position.temperature, low, high)
        return _thermal_color(t)

    if layer == Layer.PRECIPITATION:
        low, high = ranges["precipitation"]
        t = _normalize(position.precipitation, low, high)
        return _lerp_color((194, 145, 80), (30, 90, 200), t)

    if layer == Layer.SAVAGERY:
        t = max(0.0, min(1.0, position.savagery))
        return _lerp_color((25, 35, 60), (180, 60, 25), t)

    if layer == Layer.ALIGNMENT:
        t = (position.alignment + 1.0) * 0.5
        return _lerp_color((70, 40, 140), (230, 220, 95), t)

    if layer == Layer.BIOMES:
        biome = _dominant_biome(tile)
        if biome is None:
            return (80, 80, 80)
        return _biome_color(biome)

    if layer == Layer.HYDROLOGY:
        if not position.is_land:
            return WATER_COLOR
        if position.is_lake:
            return LAKE_COLOR
        if position.is_river:
            return RIVER_COLOR
        low, high = ranges["drainage"]
        t = _normalize(float(position.drainage_tiles), low, high)
        return _lerp_color((200, 200, 180), (30, 80, 180), t)

    if layer == Layer.RIVERS:
        if position.is_river:
            return RIVER_COLOR
        if water is not None:
            return water
        low, high = ranges["elevation"]
        t = _normalize(position.z, low, high)
        return _lerp_color((30, 80, 40), (220, 210, 180), t)

    if layer == Layer.LANDMASSES:
        if not position.is_land:
            return WATER_COLOR
        hue = ((position.landmass_id + 1) * 0.6180339887) % 1.0
        saturation = (0.3, 0.5, 0.7, 0.9)[min(position.landmass_class, 3)]
        red, green, blue = colorsys.hsv_to_rgb(hue, saturation, 0.85)
        return int(red * 255), int(green * 255), int(blue * 255)

    if layer == Layer.MESH and world_data.mesh is not None and mesh_index is not None:
        fx = (position.x + 0.5) / world_data.size * world_data.mesh.width
        fy = (position.y + 0.5) / world_data.size * world_data.mesh.height
        cell_id = mesh_index.nearest_cell_id(fx, fy)
        hue = (cell_id * 0.6180339887) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
        return int(red * 255), int(green * 255), int(blue * 255)

    return (0, 0, 0)


def compute_ranges(grid: list[GridTileData]) -> dict[str, tuple[float, float]]:
    return {
        "elevation": _scalar_range(grid, lambda tile: tile.position.z),
        "temperature": _scalar_range(grid, lambda tile: tile.position.temperature),
        "precipitation": _scalar_range(grid, lambda tile: tile.position.precipitation),
        "savagery": _scalar_range(grid, lambda tile: tile.position.savagery),
        "alignment": _scalar_range(grid, lambda tile: tile.position.alignment),
        "drainage": _scalar_range(
            [tile for tile in grid if tile.position.is_land] or grid,
            lambda tile: float(tile.position.drainage_tiles),
        ),
    }


def rasterize(
    world_data: WorldData,
    layer: Layer,
) -> dict[RGB, list[tuple[int, int]]]:
    ranges = compute_ranges(world_data.grid)
    mesh_index = (
        VoronoiMeshIndex(world_data.mesh)
        if layer == Layer.MESH and world_data.mesh is not None
        else None
    )
    pixels: dict[RGB, list[tuple[int, int]]] = {}
    for tile in world_data.grid:
        color = tile_color(tile, layer, ranges, world_data, mesh_index)
        pixels.setdefault(color, []).append((tile.position.x, tile.position.y))
    return pixels


def rasterize_grid(
    world_data: WorldData,
    layer: Layer,
) -> list[list[RGB]]:
    """Dense size x size color grid (row-major by y then x)."""
    size = world_data.size
    grid = [[(0, 0, 0) for _ in range(size)] for _ in range(size)]
    for color, coords in rasterize(world_data, layer).items():
        for x, y in coords:
            grid[y][x] = color
    return grid
