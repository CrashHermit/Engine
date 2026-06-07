"""Biome names and the climate × terrain resolution pipeline."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from src.core.model.climate import Precipitation, Temperature
from src.core.model.environment import EnvironmentData
from src.core.model.terrain import Depth, Elevation, Hydrology, WaterDepth


class Biome(StrEnum):
    # ── Climate grid (5×5: temperature × precipitation) ───────────────────
    POLAR_DESERT = "polar_desert"
    POLAR_BARRENS = "polar_barrens"
    TUNDRA = "tundra"
    SNOWY_TUNDRA = "snowy_tundra"
    FEN = "fen"
    COLD_DESERT = "cold_desert"
    STEPPE = "steppe"
    TAIGA = "taiga"
    BOREAL_FOREST = "boreal_forest"
    BOG = "bog"
    SCRUBLAND = "scrubland"
    PRAIRIE = "prairie"
    TEMPERATE_FOREST = "temperate_forest"
    TEMPERATE_RAINFOREST = "temperate_rainforest"
    MARSH = "marsh"
    DESERT = "desert"
    SEMI_DESERT = "semi_desert"
    SAVANNA = "savanna"
    TROPICAL_WOODLAND = "tropical_woodland"
    SEASONAL_JUNGLE = "seasonal_jungle"
    DUNE_SEA = "dune_sea"
    THORN_SCRUB = "thorn_scrub"
    BUSHVELD = "bushveld"
    MONSOON_FOREST = "monsoon_forest"
    RAINFOREST = "rainforest"
    # ── Elevation biomes (high-elevation anchors) ───────────────────────────
    MOOR = "moor"
    MONTANE_FOREST = "montane_forest"
    ALPINE_TUNDRA = "alpine_tundra"
    GLACIER = "glacier"
    # ── Shore grid (hydrology × elevation) ──────────────────────────────────
    BEACH = "beach"
    SEA_CLIFF = "sea_cliff"
    HEADLAND = "headland"
    TIDAL_FLAT = "tidal_flat"
    # ── Aquatic overrides (hydrology grid) ──────────────────────────────────
    BROOK = "brook"
    RIVER = "river"
    LAKE = "lake"
    ESTUARY = "estuary"
    LITTORAL = "littoral"
    KELP_FOREST = "kelp_forest"
    CORAL_REEF = "coral_reef"
    OPEN_OCEAN = "open_ocean"
    POLAR_SEA = "polar_sea"
    ICE_SHELF = "ice_shelf"
    # ── Underground (depth 0–4) ─────────────────────────────────────────────
    ABYSS = "abyss"
    DEEP_CAVERN = "deep_cavern"
    CAVERN = "cavern"
    CELLAR = "cellar"
    CRYPT = "crypt"


BIOME: dict[Biome, str] = {
    Biome.POLAR_DESERT: "ice and bare rock; hyper-arid cold",
    Biome.POLAR_BARRENS: "frozen wasteland; dry wind, no snowpack",
    Biome.TUNDRA: "permafrost, moss, dwarf shrubs",
    Biome.SNOWY_TUNDRA: "persistent snow; brief thaw",
    Biome.FEN: "cold sodden flats; seasonal ice and standing water",
    Biome.COLD_DESERT: "high cold barrens; dry, sparse life",
    Biome.STEPPE: "open continental grass; hard winters",
    Biome.TAIGA: "boreal conifer belt; long cold season",
    Biome.BOREAL_FOREST: "wet boreal woods; snow-heavy",
    Biome.BOG: "peat mire; cold, acid, sodden",
    Biome.SCRUBLAND: "dry shrubs, chaparral, thornbrush",
    Biome.PRAIRIE: "open temperate grass; few trees",
    Biome.TEMPERATE_FOREST: "deciduous and mixed woods; four seasons",
    Biome.TEMPERATE_RAINFOREST: "wet mild woods; year-round green",
    Biome.MARSH: "reedbeds, warm standing water",
    Biome.DESERT: "sand and stone; warm aridity",
    Biome.SEMI_DESERT: "arid fringe; scrub and bare ground",
    Biome.SAVANNA: "grass with scattered trees; dry season",
    Biome.TROPICAL_WOODLAND: "open tropical trees; reliable rain",
    Biome.SEASONAL_JUNGLE: "wet-season dense growth; dry lull",
    Biome.DUNE_SEA: "hyper-arid dunes; relentless sun",
    Biome.THORN_SCRUB: "hot dry thornbelt; brutal heat",
    Biome.BUSHVELD: "hot grass-shrub; seasonal rhythm",
    Biome.MONSOON_FOREST: "burst-green canopy; heavy wet season",
    Biome.RAINFOREST: "dense equatorial canopy; constant moisture",
    Biome.MOOR: "open high wet heath; wind, peat, low growth",
    Biome.MONTANE_FOREST: "mountain woods; cooler, steeper",
    Biome.ALPINE_TUNDRA: "above treeline; rock, snow, hardy mats",
    Biome.GLACIER: "permanent ice on peaks",
    Biome.BEACH: "sandy shore; dunes, surf line, tidal pools",
    Biome.SEA_CLIFF: "sea cliff; drop to water, spray, wind-exposed rock",
    Biome.HEADLAND: "rocky promontory; cape or point into open water",
    Biome.TIDAL_FLAT: "tidal flat; mud, salt marsh edge, channels at low tide",
    Biome.BROOK: "creek, riffle; wadeable freshwater flow",
    Biome.RIVER: "strong current; ford, bridge, or boat",
    Biome.LAKE: "standing freshwater; wind, waves, reeds",
    Biome.ESTUARY: "brackish tidal mix; mudflats, salt marsh edge",
    Biome.LITTORAL: "nearshore salt water; swell, spray, tides",
    Biome.KELP_FOREST: "cool shallow sea; kelp, urchins, seals",
    Biome.CORAL_REEF: "warm shallow sea; reef, bright fish",
    Biome.OPEN_OCEAN: "pelagic deep water; no land in sight",
    Biome.POLAR_SEA: "freezing salt water; pack ice, bitter cold",
    Biome.ICE_SHELF: "frozen-over freshwater; creaking ice",
    Biome.ABYSS: "abyssal vaults; days from daylight",
    Biome.DEEP_CAVERN: "established deep halls; mines, cisterns",
    Biome.CAVERN: "typical underground; sewers, natural caves",
    Biome.CELLAR: "shallow underworks; basements, service tunnels",
    Biome.CRYPT: "subgrade; crypts, sunken passages near the street",
}


class Resolver(Protocol):
    """One stage of biome resolution: claim a tile, or pass to the next."""

    def resolve(self, env: EnvironmentData) -> Biome | None: ...


def _squared_distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b, strict=True))


@dataclass(frozen=True)
class Lookup[K]:
    """Claim a tile by exact table lookup on a categorical key.

    The table's own keyset is the domain of applicability: a missing key (or a
    failing ``when`` guard) returns ``None`` and passes the tile along. This is
    the right primitive for features that are types rather than scales —
    hydrology, depth — where "nearest" is meaningless and only exact matches
    make sense.
    """

    key: Callable[[EnvironmentData], K]
    table: Mapping[K, Biome]
    when: Callable[[EnvironmentData], bool] = field(default=lambda env: True)

    def resolve(self, env: EnvironmentData) -> Biome | None:
        if not self.when(env):
            return None
        return self.table.get(self.key(env))


@dataclass(frozen=True)
class Geometric:
    """Claim a tile by its nearest anchor across ordinal axes.

    The right primitive for features where "between" is meaningful, so a point
    off the authored anchors falls to its closest neighbour. Total — every point
    has a nearest anchor — so this is always the terminal resolver.
    """

    anchors: Mapping[Biome, tuple[float, ...]]
    project: Callable[[EnvironmentData], tuple[float, ...]]

    def resolve(self, env: EnvironmentData) -> Biome:
        point = self.project(env)
        return min(
            self.anchors,
            key=lambda biome: _squared_distance(self.anchors[biome], point),
        )


def _hydrology(env: EnvironmentData) -> Hydrology:
    return env.terrain.hydrology


def _hydrology_temperature(env: EnvironmentData) -> tuple[Hydrology, Temperature]:
    return (env.terrain.hydrology, env.climate.temperature)


def _depth(env: EnvironmentData) -> Depth | None:
    return env.terrain.depth


def _is_shallow(env: EnvironmentData) -> bool:
    return env.terrain.water_depth == WaterDepth.SHALLOW


def _surface_point(env: EnvironmentData) -> tuple[float, float, float]:
    return (
        float(env.climate.temperature),
        float(env.climate.precipitation),
        float(env.terrain.elevation),
    )


def _anchor(
    temperature: Temperature,
    precipitation: Precipitation,
    elevation: Elevation,
) -> tuple[float, float, float]:
    """Read the (temperature, precipitation, elevation) coordinate triple."""
    return (float(temperature), float(precipitation), float(elevation))


class BiomeMatrix:
    """Resolve a biome by running an environment through a resolver pipeline.

    Resolution is a priority pipeline of two primitives. Shore, aquatic, and
    subterranean tiles are categorical and resolve by ``Lookup``; the open-air
    surface is ordinal and resolves by ``Geometric`` nearest-anchor. The first
    resolver to claim the tile wins, and the surface resolver is total, so it
    sits last as the fallback.

    The surface is a 5x5x5 cube: temperature, precipitation, and elevation are
    each a 0-4 band scale, and the enum values are the coordinates themselves.
    The climate grid anchors 25 biomes on the midland plane; four elevation
    biomes anchor higher up. Band inputs reproduce the grid exactly while
    interpolated inputs fall to the closest neighbour.
    """

    # ── Surface climate grid (5×5: temperature × precipitation) ───────────────
    _SURFACE_GRID: dict[tuple[Temperature, Precipitation], Biome] = {
        (Temperature.FREEZING, Precipitation.ARID): Biome.POLAR_DESERT,
        (Temperature.FREEZING, Precipitation.DRY): Biome.POLAR_BARRENS,
        (Temperature.FREEZING, Precipitation.SEASONAL): Biome.TUNDRA,
        (Temperature.FREEZING, Precipitation.WET): Biome.SNOWY_TUNDRA,
        (Temperature.FREEZING, Precipitation.DELUGE): Biome.FEN,
        (Temperature.COOL, Precipitation.ARID): Biome.COLD_DESERT,
        (Temperature.COOL, Precipitation.DRY): Biome.STEPPE,
        (Temperature.COOL, Precipitation.SEASONAL): Biome.TAIGA,
        (Temperature.COOL, Precipitation.WET): Biome.BOREAL_FOREST,
        (Temperature.COOL, Precipitation.DELUGE): Biome.BOG,
        (Temperature.MILD, Precipitation.ARID): Biome.SCRUBLAND,
        (Temperature.MILD, Precipitation.DRY): Biome.PRAIRIE,
        (Temperature.MILD, Precipitation.SEASONAL): Biome.TEMPERATE_FOREST,
        (Temperature.MILD, Precipitation.WET): Biome.TEMPERATE_RAINFOREST,
        (Temperature.MILD, Precipitation.DELUGE): Biome.MARSH,
        (Temperature.WARM, Precipitation.ARID): Biome.DESERT,
        (Temperature.WARM, Precipitation.DRY): Biome.SEMI_DESERT,
        (Temperature.WARM, Precipitation.SEASONAL): Biome.SAVANNA,
        (Temperature.WARM, Precipitation.WET): Biome.TROPICAL_WOODLAND,
        (Temperature.WARM, Precipitation.DELUGE): Biome.SEASONAL_JUNGLE,
        (Temperature.HOT, Precipitation.ARID): Biome.DUNE_SEA,
        (Temperature.HOT, Precipitation.DRY): Biome.THORN_SCRUB,
        (Temperature.HOT, Precipitation.SEASONAL): Biome.BUSHVELD,
        (Temperature.HOT, Precipitation.WET): Biome.MONSOON_FOREST,
        (Temperature.HOT, Precipitation.DELUGE): Biome.RAINFOREST,
    }

    # The climate biomes anchor at this default elevation; tiles here reproduce
    # the climate grid exactly. The four elevation biomes anchor higher up.
    _DEFAULT_ELEVATION: Elevation = Elevation.MIDLAND

    # The four elevation biomes, anchored high in the matrix instead of resolved
    # by a separate override pass: (temperature, precipitation, elevation) centre.
    # At the peak, temperature alone separates glacier, alpine tundra, and the
    # montane/moor pair a step below.
    _ELEVATION_ANCHORS: dict[Biome, tuple[Temperature, Precipitation, Elevation]] = {
        Biome.MONTANE_FOREST: (
            Temperature.MILD,
            Precipitation.WET,
            Elevation.HIGHLAND,
        ),
        Biome.MOOR: (Temperature.COOL, Precipitation.DELUGE, Elevation.HIGHLAND),
        Biome.ALPINE_TUNDRA: (
            Temperature.COOL,
            Precipitation.SEASONAL,
            Elevation.SUMMIT,
        ),
        Biome.GLACIER: (Temperature.FREEZING, Precipitation.SEASONAL, Elevation.SUMMIT),
    }

    # Shore biome is a function of the shore hydrology alone.
    _SHORE_GRID: dict[Hydrology, Biome] = {
        Hydrology.BEACH: Biome.BEACH,
        Hydrology.CLIFF: Biome.SEA_CLIFF,
        Hydrology.HEADLAND: Biome.HEADLAND,
        Hydrology.TIDAL_FLAT: Biome.TIDAL_FLAT,
    }

    # ── Aquatic grid (hydrology × temperature) ────────────────────────────────
    # Standing fresh water freezes to ice; salt water freezes to polar sea and
    # opens to ocean offshore. The shallow overlay below adds reefs and kelp.
    _AQUATIC_GRID: dict[tuple[Hydrology, Temperature], Biome] = {
        (Hydrology.STREAM, Temperature.FREEZING): Biome.BROOK,
        (Hydrology.STREAM, Temperature.COOL): Biome.BROOK,
        (Hydrology.STREAM, Temperature.MILD): Biome.BROOK,
        (Hydrology.STREAM, Temperature.WARM): Biome.BROOK,
        (Hydrology.STREAM, Temperature.HOT): Biome.BROOK,
        (Hydrology.RIVER, Temperature.FREEZING): Biome.ICE_SHELF,
        (Hydrology.RIVER, Temperature.COOL): Biome.RIVER,
        (Hydrology.RIVER, Temperature.MILD): Biome.RIVER,
        (Hydrology.RIVER, Temperature.WARM): Biome.RIVER,
        (Hydrology.RIVER, Temperature.HOT): Biome.RIVER,
        (Hydrology.LAKE, Temperature.FREEZING): Biome.ICE_SHELF,
        (Hydrology.LAKE, Temperature.COOL): Biome.LAKE,
        (Hydrology.LAKE, Temperature.MILD): Biome.LAKE,
        (Hydrology.LAKE, Temperature.WARM): Biome.LAKE,
        (Hydrology.LAKE, Temperature.HOT): Biome.LAKE,
        (Hydrology.INLAND_SEA, Temperature.FREEZING): Biome.ICE_SHELF,
        (Hydrology.INLAND_SEA, Temperature.COOL): Biome.LAKE,
        (Hydrology.INLAND_SEA, Temperature.MILD): Biome.LAKE,
        (Hydrology.INLAND_SEA, Temperature.WARM): Biome.LAKE,
        (Hydrology.INLAND_SEA, Temperature.HOT): Biome.LAKE,
        (Hydrology.ESTUARY, Temperature.FREEZING): Biome.ESTUARY,
        (Hydrology.ESTUARY, Temperature.COOL): Biome.ESTUARY,
        (Hydrology.ESTUARY, Temperature.MILD): Biome.ESTUARY,
        (Hydrology.ESTUARY, Temperature.WARM): Biome.ESTUARY,
        (Hydrology.ESTUARY, Temperature.HOT): Biome.ESTUARY,
        (Hydrology.SEA, Temperature.FREEZING): Biome.POLAR_SEA,
        (Hydrology.SEA, Temperature.COOL): Biome.LITTORAL,
        (Hydrology.SEA, Temperature.MILD): Biome.LITTORAL,
        (Hydrology.SEA, Temperature.WARM): Biome.LITTORAL,
        (Hydrology.SEA, Temperature.HOT): Biome.LITTORAL,
        (Hydrology.OCEAN, Temperature.FREEZING): Biome.POLAR_SEA,
        (Hydrology.OCEAN, Temperature.COOL): Biome.OPEN_OCEAN,
        (Hydrology.OCEAN, Temperature.MILD): Biome.OPEN_OCEAN,
        (Hydrology.OCEAN, Temperature.WARM): Biome.OPEN_OCEAN,
        (Hydrology.OCEAN, Temperature.HOT): Biome.OPEN_OCEAN,
    }

    # Shallow salt water grows reefs and kelp; consulted only when shallow, and
    # falls through to the aquatic grid for any pair it does not cover.
    _SHALLOW_SEA_GRID: dict[tuple[Hydrology, Temperature], Biome] = {
        (Hydrology.SEA, Temperature.COOL): Biome.KELP_FOREST,
        (Hydrology.SEA, Temperature.WARM): Biome.CORAL_REEF,
        (Hydrology.SEA, Temperature.HOT): Biome.CORAL_REEF,
    }

    _SUBTERRANEAN_GRID: dict[Depth, Biome] = {
        Depth.SUBGRADE: Biome.CRYPT,
        Depth.SHALLOW: Biome.CELLAR,
        Depth.LOW: Biome.CAVERN,
        Depth.DEEP: Biome.DEEP_CAVERN,
        Depth.ABYSSAL: Biome.ABYSS,
    }

    def __init__(self) -> None:
        # Priority pipeline; first resolver to claim the tile wins. The shallow
        # overlay precedes open water so reefs and kelp beat plain littoral, and
        # every water/underground stage precedes the total surface fallback.
        self._pipeline: tuple[Resolver, ...] = (
            Lookup(key=_hydrology, table=self._SHORE_GRID),
            Lookup(
                key=_hydrology_temperature,
                table=self._SHALLOW_SEA_GRID,
                when=_is_shallow,
            ),
            Lookup(key=_hydrology_temperature, table=self._AQUATIC_GRID),
            Lookup(key=_depth, table=self._SUBTERRANEAN_GRID),
            Geometric(anchors=self._build_anchors(), project=_surface_point),
        )

    def resolve(self, env: EnvironmentData) -> Biome:
        """Resolve the biome for an environment by running the pipeline."""
        for resolver in self._pipeline:
            biome = resolver.resolve(env)
            if biome is not None:
                return biome
        raise AssertionError("the geometric resolver is total")

    def _build_anchors(self) -> dict[Biome, tuple[float, float, float]]:
        anchors = {
            biome: _anchor(temperature, precipitation, self._DEFAULT_ELEVATION)
            for (temperature, precipitation), biome in self._SURFACE_GRID.items()
        }
        for biome, (
            temperature,
            precipitation,
            elevation,
        ) in self._ELEVATION_ANCHORS.items():
            anchors[biome] = _anchor(temperature, precipitation, elevation)
        return anchors


BIOME_MATRIX = BiomeMatrix()
