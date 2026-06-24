from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from src.worldgen.bake import bake_to_grid, nearest_cell_per_tile, stamp_rivers
from src.worldgen.context import WorldContext
from src.worldgen.fields import GridFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.types import Float64Array, Int32Array

type RGB = tuple[int, int, int]

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
    LATITUDE = "latitude"
    INSOLATION = "insolation"
    TEMPERATURE = "temperature"
    SST = "sst"
    SST_ANOMALY = "sst_anomaly"
    WIND = "wind"
    CONVERGENCE = "convergence"
    PRECIPITATION = "precipitation"
    DISCHARGE = "discharge"
    VOLCANISM = "volcanism"
    SAVAGERY = "savagery"
    MAGIC_STRENGTH = "magic_strength"
    MAGIC_VALENCE = "magic_valence"
    MAGIC_CHANNELS = "magic_channels"
    BIOMES = "biomes"
    REGIONS = "regions"


# Layers grouped by the pipeline phase that produces them — the single source of
# truth for both ordering and the viewer's section headers.  ``LAYER_ORDER`` is
# the flattened sequence (used for export, cycling, and indexing).
LAYER_GROUPS: tuple[tuple[str, tuple[Layer, ...]], ...] = (
    (
        "Terrain",
        (
            Layer.ELEVATION,
            Layer.LAND,
            Layer.PLATES,
            Layer.UPLIFT,
            Layer.DRAINAGE,
            Layer.VOLCANISM,
            Layer.MESH,
        ),
    ),
    (
        "Climate",
        (
            Layer.LATITUDE,
            Layer.INSOLATION,
            Layer.TEMPERATURE,
            Layer.SST,
            Layer.SST_ANOMALY,
            Layer.WIND,
            Layer.CONVERGENCE,
            Layer.PRECIPITATION,
        ),
    ),
    (
        "Water",
        (Layer.DISCHARGE,),
    ),
    (
        "Magic & Ecology",
        (
            Layer.SAVAGERY,
            Layer.MAGIC_STRENGTH,
            Layer.MAGIC_VALENCE,
            Layer.MAGIC_CHANNELS,
            Layer.BIOMES,
        ),
    ),
    (
        "Regions",
        (Layer.REGIONS,),
    ),
)

LAYER_ORDER: tuple[Layer, ...] = tuple(
    layer for _group, layers in LAYER_GROUPS for layer in layers
)

LAYER_LABELS: dict[Layer, str] = {
    Layer.ELEVATION: "Elevation",
    Layer.LAND: "Land",
    Layer.MESH: "Mesh debug",
    Layer.PLATES: "Plates",
    Layer.UPLIFT: "Uplift",
    Layer.DRAINAGE: "Drainage",
    Layer.LATITUDE: "Latitude",
    Layer.INSOLATION: "Insolation",
    Layer.TEMPERATURE: "Temperature",
    Layer.SST: "Sea temperature",
    Layer.SST_ANOMALY: "Current anomaly",
    Layer.WIND: "Wind",
    Layer.CONVERGENCE: "Convergence",
    Layer.PRECIPITATION: "Precipitation",
    Layer.DISCHARGE: "Discharge",
    Layer.VOLCANISM: "Volcanism",
    Layer.SAVAGERY: "Savagery",
    Layer.MAGIC_STRENGTH: "Magic strength",
    Layer.MAGIC_VALENCE: "Magic valence",
    Layer.MAGIC_CHANNELS: "Magic channels",
    Layer.BIOMES: "Biomes",
    Layer.REGIONS: "Regions",
}

LAYER_DESCRIPTIONS: dict[Layer, str] = {
    Layer.ELEVATION: "Terrain height. Dark blue = ocean, green = low land, tan = high land.",
    Layer.LAND: "Land vs ocean.",
    Layer.MESH: "Debug: each color is a Voronoi cell id (verify periodic sampling).",
    Layer.PLATES: "Tectonic plates; each color is a plate id (ragged Voronoi partition).",
    Layer.UPLIFT: "Base tectonic uplift before boundary belts. Bright = continental plates, dark = oceanic.",
    Layer.DRAINAGE: "Upstream drainage area per cell (log). Brighter = more flow. River valleys visible as bright veins.",
    Layer.LATITUDE: "Signed latitude [-1,1]. Equator (pale) at map center; hemispheres diverge red (north) / blue (south) toward the shared polar seam.",
    Layer.INSOLATION: "Authored energy field. Bright = hot sunband, dark = cold frostbelt; wraps seamlessly.",
    Layer.TEMPERATURE: "Warmth [0,1]. Cold frostbelt and mountain peaks blue; hot sunband red; mild coasts.",
    Layer.SST: "Sea-surface temperature [0,1]. Wind-advected ocean currents: warm water carried poleward, cold equatorward; land shows its baseline.",
    Layer.SST_ANOMALY: "Current warming/cooling: SST minus latitude baseline. Red = warm current, blue = cold current/upwelling; land neutral.",
    Layer.WIND: "Wind: hue = direction (atan2 v,u), brightness = speed. Belts deflect around ranges.",
    Layer.CONVERGENCE: "Signed vertical motion [-1,1]. Blue = rising/converging air (ITCZ, subpolar lows, windward ranges) that rains; tan = sinking/diverging (subtropical deserts).",
    Layer.PRECIPITATION: "Rainfall [0,1]. Wet windward coasts bright; dry interiors and rain shadows dark.",
    Layer.DISCHARGE: "Rain-weighted water flow (log). Brighter = more water. River valleys glow brighter in wet regions.",
    Layer.VOLCANISM: "Present-day volcanic activity [0,1]. Bright subduction arcs, hotspot trails, and mid-ocean ridges; dark elsewhere.",
    Layer.SAVAGERY: "Legible danger [0,1]. Bright deep interiors, deserts, frostbelt, and ranges; calm temperate coasts.",
    Layer.MAGIC_STRENGTH: "Leyline intensity [0,1]. Bright web of lines between nexuses; dim floor elsewhere.",
    Layer.MAGIC_VALENCE: "Magic valence [-1,1]. Diverging palette: corrupt (magenta) vs pure (cyan); neutral grey off the web.",
    Layer.MAGIC_CHANNELS: "Channel composition (corpus/mens/anima) mapped straight to RGB.",
    Layer.BIOMES: "Dominant biome per tile (argmax of the soft weights); one hue per biome.",
    Layer.REGIONS: "Named geographic regions (the gameplay socket); one hue per region id (landmasses + ocean bodies).",
}


def generate_world(
    size: int, seed: int, resolution: int | None = None
) -> Phase0World:
    """Run the full pipeline and bake mesh fields for display.

    ``resolution`` decouples render detail from the gameplay ``size``: the
    mesh is baked onto a ``resolution × resolution`` grid instead of
    ``size × size``, so diagnostic PNGs can resolve the full Voronoi mesh
    (up to ``cell_count`` cells) instead of the coarse gameplay grid.  When
    ``None`` (the interactive default), detail equals the gameplay ``size``.
    """
    ctx: WorldContext
    _world, ctx = WorldgenPipeline().run_debug(seed=seed, size=size)

    render_size: int = resolution if resolution is not None else ctx.config.size
    nearest: Int32Array = nearest_cell_per_tile(
        geometry=ctx.geometry,
        size=render_size,
    )
    # Bake the mesh fields at the render resolution, then stamp rivers crisply
    # at that resolution (the product grid bakes at gameplay size; this is a
    # diagnostic re-bake that keeps sub-tile detail).
    grid: GridFields = bake_to_grid(fields=ctx.fields, nearest=nearest)
    if ctx.rivers:
        stamp_rivers(
            grid=grid,
            rivers=ctx.rivers,
            geometry=ctx.geometry,
            fields=ctx.fields,
            size=render_size,
            cfg=ctx.config.river,
        )

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
        size=render_size,
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
        return _hypsometric_color(t)

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

    if layer == Layer.LATITUDE:
        lat: float = float(grid.latitude[tile_index])  # [-1, 1]
        # Equator pale; north warms red, south cools blue (hemisphere structure).
        if lat >= 0.0:
            return _lerp_color(low=(235, 235, 235), high=(200, 60, 60), t=lat)
        return _lerp_color(low=(235, 235, 235), high=(60, 90, 200), t=-lat)

    if layer == Layer.TEMPERATURE:
        t: float = max(0.0, min(1.0, float(grid.temperature[tile_index])))
        # cold = blue, mild = pale, hot = red
        return _lerp_color(low=(40, 80, 200), high=(220, 60, 50), t=t)

    if layer == Layer.SST:
        t: float = max(0.0, min(1.0, float(grid.sst[tile_index])))
        return _lerp_color(low=(40, 80, 200), high=(220, 60, 50), t=t)

    if layer == Layer.SST_ANOMALY:
        # SST minus latitude baseline: warm current (red) vs cold current (blue).
        anomaly: float = float(grid.sst[tile_index]) - float(
            world.insolation[tile_index]
        )
        # ±0.2 spans the palette; neutral grey at 0.
        t: float = max(-1.0, min(1.0, anomaly / 0.2))
        if t >= 0.0:
            return _lerp_color(low=(120, 120, 120), high=(220, 60, 50), t=t)
        return _lerp_color(low=(120, 120, 120), high=(40, 80, 200), t=-t)

    if layer == Layer.CONVERGENCE:
        v: float = max(-1.0, min(1.0, float(grid.convergence[tile_index])))
        # rising/converging = blue (wet); sinking/diverging = tan (dry); neutral grey
        if v >= 0.0:
            return _lerp_color(low=(150, 140, 120), high=(40, 90, 200), t=v)
        return _lerp_color(low=(150, 140, 120), high=(185, 160, 110), t=-v)

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

    if layer == Layer.VOLCANISM:
        t: float = max(0.0, min(1.0, float(grid.volcanism[tile_index])))
        # cold basalt -> molten orange
        return _lerp_color(low=(20, 18, 24), high=(255, 110, 20), t=t)

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
        red, green, blue = _biome_palette()[biome_col]
        return int(red), int(green), int(blue)

    if layer == Layer.REGIONS:
        region: int = int(grid.region_id[tile_index])
        if region < 0:
            return (20, 20, 25)
        hue: float = (region * 0.6180339887) % 1.0
        red, green, blue = colorsys.hsv_to_rgb(h=hue, s=0.65, v=0.9)
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
    # Land-normalized elevation (0..land-max) so the hypsometric tint resolves real
    # relief instead of squashing all land into the top of the ramp.
    land_z = grid.elevation[grid.is_land.astype(bool)]
    z_min: float = 0.0
    z_max: float = float(land_z.max()) if land_z.size else 1.0
    z_span: float = z_max if z_max > 0.0 else 1.0

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


# ---------------------------------------------------------------------------
# Vectorized dense renderer (for high-resolution PNG export)
# ---------------------------------------------------------------------------
#
# rasterize_grid colors one tile at a time in Python — fine for the small
# interactive canvas, far too slow for a 2048x2048 diagnostic export. The
# functions below colour every tile at once with numpy, producing the same
# colours as _tile_color but in milliseconds. The viewer keeps the scalar path.


def _lerp_arr(low: RGB, high: RGB, t: Float64Array) -> Float64Array:
    """Per-element lerp between two RGB colors; returns an (n, 3) float array."""
    t = np.clip(t, 0.0, 1.0)[:, None]
    low_arr = np.array(low, dtype=np.float64)[None, :]
    high_arr = np.array(high, dtype=np.float64)[None, :]
    return low_arr + (high_arr - low_arr) * t


def _hsv_to_rgb(
    h: Float64Array, s: Float64Array, v: Float64Array
) -> Float64Array:
    """Vectorized HSV→RGB; inputs in [0, 1], returns (n, 3) in [0, 255]."""
    h6 = (h % 1.0) * 6.0
    i = np.floor(h6).astype(np.int64) % 6
    f = h6 - np.floor(h6)
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=1) * 255.0


_PHI: float = 0.6180339887


# Hypsometric land tint (green lowland → yellow → brown upland → white peak),
# normalized over 0..land-max so real relief reads instead of squashing land into
# the top of a single ramp (the relief is in the data; only the old colormap hid it).
_HYPS_STOPS: Float64Array = np.array([0.0, 0.35, 0.6, 0.85, 1.0])
_HYPS_COLORS: Float64Array = np.array(
    [
        [60, 130, 60],     # low green
        [180, 190, 90],    # yellow-green
        [150, 110, 70],    # brown upland
        [120, 100, 95],    # dark rocky
        [245, 245, 245],   # snow peak
    ],
    dtype=np.float64,
)


def _hypsometric(t: Float64Array) -> Float64Array:
    """Map land elevation fraction ``t`` in [0, 1] to an (n, 3) hypsometric tint."""
    t = np.clip(t, 0.0, 1.0)
    return np.stack(
        [np.interp(t, _HYPS_STOPS, _HYPS_COLORS[:, c]) for c in range(3)], axis=1
    )


def _hypsometric_color(t: float) -> RGB:
    """Scalar hypsometric tint for the interactive per-tile path."""
    tc: float = max(0.0, min(1.0, t))
    return (
        int(np.interp(tc, _HYPS_STOPS, _HYPS_COLORS[:, 0])),
        int(np.interp(tc, _HYPS_STOPS, _HYPS_COLORS[:, 1])),
        int(np.interp(tc, _HYPS_STOPS, _HYPS_COLORS[:, 2])),
    )


# 2-D climate colormap for biomes: each biome is colored by its (temperature,
# precipitation) center so climatically-adjacent biomes are perceptually adjacent
# and the map reads as a smooth climate field — an honest view of coherence,
# versus golden-ratio hues that paint real ecotones as collisions.  Bilinear blend
# over four climate-corner colors; viewer-only (these hues don't ship).
_BIOME_C00: Float64Array = np.array([210, 215, 205], dtype=np.float64)  # cold + dry
_BIOME_C10: Float64Array = np.array([225, 200, 120], dtype=np.float64)  # hot + dry
_BIOME_C01: Float64Array = np.array([70, 110, 120], dtype=np.float64)   # cold + wet
_BIOME_C11: Float64Array = np.array([25, 115, 45], dtype=np.float64)    # hot + wet


def _biome_palette() -> Float64Array:
    """Per-biome-column RGB palette from climate centers; shape ``(n_biomes, 3)``."""
    from src.worldgen.ecology.biomes import derive_centers

    center_temp, center_precip, _order = derive_centers()
    t: Float64Array = center_temp[:, None]
    p: Float64Array = center_precip[:, None]
    return (
        (1.0 - t) * (1.0 - p) * _BIOME_C00
        + t * (1.0 - p) * _BIOME_C10
        + (1.0 - t) * p * _BIOME_C01
        + t * p * _BIOME_C11
    )


def colorize(world: Phase0World, layer: Layer) -> Float64Array:
    """Color every tile for ``layer`` at once; returns (n, 3) uint8, flat tile order."""
    grid: GridFields = world.grid
    n: int = world.size * world.size
    is_land: np.ndarray = grid.is_land.astype(bool)
    out: Float64Array = np.zeros((n, 3), dtype=np.float64)

    if layer == Layer.LAND:
        out[:] = np.array(LAND_COLOR)
        out[~is_land] = np.array(WATER_COLOR)

    elif layer == Layer.ELEVATION:
        z = grid.elevation.astype(np.float64)
        land_z = z[is_land]
        z_max = float(land_z.max()) if land_z.size else 1.0
        span = z_max if z_max > 0.0 else 1.0
        out = _hypsometric(z / span)
        out[~is_land] = np.array(WATER_COLOR)

    elif layer in (Layer.PLATES, Layer.MESH):
        ids = (grid.plate_id if layer == Layer.PLATES else world.nearest).astype(
            np.float64
        )
        hue = (ids * _PHI) % 1.0
        out = _hsv_to_rgb(hue, np.full(n, 0.7), np.full(n, 0.9))

    elif layer == Layer.UPLIFT:
        out = _lerp_arr((30, 40, 80), (220, 200, 160), grid.uplift.astype(np.float64))

    elif layer in (Layer.DRAINAGE, Layer.DISCHARGE):
        values = (
            grid.drainage if layer == Layer.DRAINAGE else grid.discharge
        ).astype(np.float64)
        scale = 1000.0 if layer == Layer.DRAINAGE else 10000.0
        low = (30, 60, 100) if layer == Layer.DRAINAGE else (30, 60, 120)
        high = (255, 240, 200) if layer == Layer.DRAINAGE else (100, 200, 255)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(values > 0.0, np.log(values) / np.log(scale), 0.0)
        out = _lerp_arr(low, high, t)
        out[(values <= 0.0) | (~is_land)] = np.array((10, 20, 30))

    elif layer == Layer.INSOLATION:
        out = _lerp_arr((20, 30, 90), (255, 240, 180), world.insolation)

    elif layer == Layer.LATITUDE:
        lat = grid.latitude.astype(np.float64)
        north = _lerp_arr((235, 235, 235), (200, 60, 60), np.clip(lat, 0.0, 1.0))
        south = _lerp_arr((235, 235, 235), (60, 90, 200), np.clip(-lat, 0.0, 1.0))
        out = np.where((lat >= 0.0)[:, None], north, south)

    elif layer == Layer.TEMPERATURE:
        out = _lerp_arr((40, 80, 200), (220, 60, 50), grid.temperature.astype(np.float64))

    elif layer == Layer.SST:
        out = _lerp_arr((40, 80, 200), (220, 60, 50), grid.sst.astype(np.float64))

    elif layer == Layer.SST_ANOMALY:
        anomaly = grid.sst.astype(np.float64) - world.insolation
        t = np.clip(anomaly / 0.2, -1.0, 1.0)
        warm = _lerp_arr((120, 120, 120), (220, 60, 50), t)
        cold = _lerp_arr((120, 120, 120), (40, 80, 200), -t)
        out = np.where((t >= 0.0)[:, None], warm, cold)

    elif layer == Layer.CONVERGENCE:
        v = np.clip(grid.convergence.astype(np.float64), -1.0, 1.0)
        rising = _lerp_arr((150, 140, 120), (40, 90, 200), np.clip(v, 0.0, 1.0))
        sinking = _lerp_arr((150, 140, 120), (185, 160, 110), np.clip(-v, 0.0, 1.0))
        out = np.where((v >= 0.0)[:, None], rising, sinking)

    elif layer == Layer.PRECIPITATION:
        out = _lerp_arr((200, 180, 120), (20, 90, 130), grid.precipitation.astype(np.float64))

    elif layer == Layer.WIND:
        u = grid.wind_u.astype(np.float64)
        v = grid.wind_v.astype(np.float64)
        mag = np.clip(grid.wind_magnitude.astype(np.float64), 0.0, 1.0)
        hue = (np.arctan2(v, u) / (2.0 * np.pi)) % 1.0
        out = _hsv_to_rgb(hue, np.full(n, 0.8), 0.2 + 0.8 * mag)

    elif layer == Layer.VOLCANISM:
        out = _lerp_arr((20, 18, 24), (255, 110, 20), grid.volcanism.astype(np.float64))

    elif layer == Layer.SAVAGERY:
        out = _lerp_arr((40, 90, 60), (200, 40, 40), grid.savagery.astype(np.float64))

    elif layer == Layer.MAGIC_STRENGTH:
        out = _lerp_arr((15, 15, 30), (180, 120, 255), grid.magic_strength.astype(np.float64))

    elif layer == Layer.MAGIC_VALENCE:
        valence = np.clip(grid.magic_valence.astype(np.float64), -1.0, 1.0)
        corrupt = _lerp_arr((120, 120, 120), (210, 40, 160), -valence)
        pure = _lerp_arr((120, 120, 120), (40, 200, 210), valence)
        out = np.where((valence < 0.0)[:, None], corrupt, pure)

    elif layer == Layer.MAGIC_CHANNELS:
        channels = grid.magic_channels.astype(np.float64)
        peak = np.maximum(channels.max(axis=1, keepdims=True), 1e-6)
        out = 255.0 * channels / peak

    elif layer == Layer.BIOMES:
        col = np.argmax(grid.biome_weights, axis=1)
        out = _biome_palette()[col]
        out[~is_land] = np.array(WATER_COLOR)

    elif layer == Layer.REGIONS:
        ids = grid.region_id.astype(np.float64)
        hue = (ids * _PHI) % 1.0
        out = _hsv_to_rgb(hue, np.full(n, 0.65), np.full(n, 0.9))
        out[ids < 0.0] = np.array((20, 20, 25))  # unassigned (should not occur)

    return np.clip(out, 0.0, 255.0).astype(np.uint8)


def rasterize_rgb(world: Phase0World, layer: Layer) -> np.ndarray:
    """Dense ``(size, size, 3)`` uint8 image array (row-major: ``[y, x]``)."""
    size: int = world.size
    flat: Float64Array = colorize(world, layer)
    # Flat tile index is x-major (x * size + y); transpose to image rows (y, x).
    return flat.reshape(size, size, 3).transpose(1, 0, 2)
