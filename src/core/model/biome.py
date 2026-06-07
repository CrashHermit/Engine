"""Biome names and the climate × terrain mapping.

Reading order: first the ``Biome`` vocabulary and its descriptions, then
``BiomeMatrix``, which turns an environment into a biome. The matrix is the
interesting part — its class docstring explains how resolution works.
"""

from __future__ import annotations

from enum import StrEnum

from src.core.model.climate import Precipitation, Temperature
from src.core.model.environment import EnvironmentData
from src.core.model.terrain import (
    Depth,
    Elevation,
    Expanse,
    Hydrology,
    Salinity,
    WaterDepth,
)


class Biome(StrEnum):
    # ── Surface climate biomes (temperature × precipitation) ─────────────────
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
    # ── Highland biomes (anchored higher in the surface cube) ────────────────
    MOOR = "moor"
    MONTANE_FOREST = "montane_forest"
    ALPINE_TUNDRA = "alpine_tundra"
    GLACIER = "glacier"
    # ── Shore biomes (one per coastline landform) ────────────────────────────
    BEACH = "beach"
    SEA_CLIFF = "sea_cliff"
    HEADLAND = "headland"
    TIDAL_FLAT = "tidal_flat"
    # ── Open-water biomes (salinity × expanse × temperature × depth) ──────────
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
    # ── Underground biomes (one per depth band) ──────────────────────────────
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


class BiomeMatrix:
    """Turn an environment into a biome.

    A tile belongs to exactly one "medium", and ``resolve`` checks them in
    priority order, returning the first that applies:

        1. shore      — a coastline landform (beach, cliff, ...)
        2. open water — a body of water (set on ``terrain.water``)
        3. underground — below the surface (set on ``terrain.depth``)
        4. surface    — open air; the fallback when none of the above apply

    Two of these are simple table lookups (shore, underground): the input maps
    straight to a biome. The other two — open water and the surface — use
    "nearest anchor": each biome is placed at a point in a small grid of ordinal
    traits (e.g. the surface grid is temperature × precipitation × elevation),
    and a tile resolves to the biome whose point is closest to its own traits.
    That is what lets a tile *between* two biomes fall to the nearer one.
    """

    # ── Data tables ───────────────────────────────────────────────────────────

    # Surface climate grid: 25 biomes, one per temperature × precipitation pair.
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

    # The 25 climate biomes above all sit at this elevation; tiles here reproduce
    # the climate grid exactly. The four highland biomes below anchor higher up.
    _DEFAULT_ELEVATION: Elevation = Elevation.MIDLAND

    # Highland biomes: (temperature, precipitation, elevation) anchor points.
    _ELEVATION_ANCHORS: dict[Biome, tuple[Temperature, Precipitation, Elevation]] = {
        Biome.MONTANE_FOREST: (Temperature.MILD, Precipitation.WET, Elevation.HIGHLAND),
        Biome.MOOR: (Temperature.COOL, Precipitation.DELUGE, Elevation.HIGHLAND),
        Biome.ALPINE_TUNDRA: (
            Temperature.COOL,
            Precipitation.SEASONAL,
            Elevation.SUMMIT,
        ),
        Biome.GLACIER: (Temperature.FREEZING, Precipitation.SEASONAL, Elevation.SUMMIT),
    }

    # Shore: each coastline landform maps straight to one biome.
    _SHORE_GRID: dict[Hydrology, Biome] = {
        Hydrology.BEACH: Biome.BEACH,
        Hydrology.CLIFF: Biome.SEA_CLIFF,
        Hydrology.HEADLAND: Biome.HEADLAND,
        Hydrology.TIDAL_FLAT: Biome.TIDAL_FLAT,
    }

    # Open-water anchors: (salinity, expanse, temperature, depth) points. Freezing
    # pulls fresh water to ice and salt water to polar sea; a shallow salt
    # nearshore warms to reef or cools to kelp — all just nearest-anchor geometry.
    _AQUATIC_ANCHORS: dict[Biome, tuple[Salinity, Expanse, Temperature, WaterDepth]] = {
        Biome.BROOK: (
            Salinity.FRESH,
            Expanse.CHANNEL,
            Temperature.MILD,
            WaterDepth.SHALLOW,
        ),
        Biome.RIVER: (
            Salinity.FRESH,
            Expanse.COURSE,
            Temperature.MILD,
            WaterDepth.DEEP,
        ),
        Biome.LAKE: (Salinity.FRESH, Expanse.BASIN, Temperature.MILD, WaterDepth.DEEP),
        Biome.ICE_SHELF: (
            Salinity.FRESH,
            Expanse.BASIN,
            Temperature.FREEZING,
            WaterDepth.DEEP,
        ),
        Biome.ESTUARY: (
            Salinity.BRACKISH,
            Expanse.BASIN,
            Temperature.MILD,
            WaterDepth.MODERATE,
        ),
        Biome.LITTORAL: (
            Salinity.SALINE,
            Expanse.NEARSHORE,
            Temperature.MILD,
            WaterDepth.DEEP,
        ),
        Biome.KELP_FOREST: (
            Salinity.SALINE,
            Expanse.NEARSHORE,
            Temperature.COOL,
            WaterDepth.SHALLOW,
        ),
        Biome.CORAL_REEF: (
            Salinity.SALINE,
            Expanse.NEARSHORE,
            Temperature.WARM,
            WaterDepth.SHALLOW,
        ),
        Biome.OPEN_OCEAN: (
            Salinity.SALINE,
            Expanse.OPEN,
            Temperature.MILD,
            WaterDepth.DEEP,
        ),
        Biome.POLAR_SEA: (
            Salinity.SALINE,
            Expanse.OPEN,
            Temperature.FREEZING,
            WaterDepth.DEEP,
        ),
    }

    # Underground: each depth band maps straight to one biome.
    _SUBTERRANEAN_GRID: dict[Depth, Biome] = {
        Depth.SUBGRADE: Biome.CRYPT,
        Depth.SHALLOW: Biome.CELLAR,
        Depth.LOW: Biome.CAVERN,
        Depth.DEEP: Biome.DEEP_CAVERN,
        Depth.ABYSSAL: Biome.ABYSS,
    }

    def __init__(self) -> None:
        # Pre-compute the nearest-anchor grids once: turn the trait tables above
        # into plain coordinate points the distance check can compare against.
        self._surface_anchors = self._build_surface_anchors()
        self._water_anchors = self._build_water_anchors()

    def resolve(self, env: EnvironmentData) -> Biome:
        """Resolve the biome for an environment (first matching medium wins)."""
        shore = self._shore_biome(env)
        if shore is not None:
            return shore
        water = self._water_biome(env)
        if water is not None:
            return water
        underground = self._underground_biome(env)
        if underground is not None:
            return underground
        return self._surface_biome(env)

    # ── One method per medium ─────────────────────────────────────────────────

    def _shore_biome(self, env: EnvironmentData) -> Biome | None:
        """Map a coastline landform straight to a biome (else no match)."""
        return self._SHORE_GRID.get(env.terrain.hydrology)

    def _water_biome(self, env: EnvironmentData) -> Biome | None:
        """Open water: the aquatic biome nearest to this body's traits."""
        water = env.terrain.water
        if water is None:
            return None
        point = (
            float(water.salinity),
            float(water.expanse),
            float(env.climate.temperature),
            float(water.depth),
        )
        return self._nearest(self._water_anchors, point)

    def _underground_biome(self, env: EnvironmentData) -> Biome | None:
        """Below ground, the depth band maps straight to a biome."""
        depth = env.terrain.depth
        if depth is None:
            return None
        return self._SUBTERRANEAN_GRID[depth]

    def _surface_biome(self, env: EnvironmentData) -> Biome:
        """Open air: the surface biome nearest to this tile's climate."""
        point = (
            float(env.climate.temperature),
            float(env.climate.precipitation),
            float(env.terrain.elevation),
        )
        return self._nearest(self._surface_anchors, point)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _nearest(
        anchors: dict[Biome, tuple[float, ...]],
        point: tuple[float, ...],
    ) -> Biome:
        """Return the biome whose anchor point is closest to ``point``."""

        def distance_to(biome: Biome) -> float:
            anchor = anchors[biome]
            return sum([(a - p) ** 2 for a, p in zip(anchor, point)])

        return min(anchors, key=distance_to)

    def _build_surface_anchors(self) -> dict[Biome, tuple[float, float, float]]:
        """Place each surface biome at its (temp, precip, elevation) point."""
        anchors: dict[Biome, tuple[float, float, float]] = {}
        for (temperature, precipitation), biome in self._SURFACE_GRID.items():
            anchors[biome] = (
                float(temperature),
                float(precipitation),
                float(self._DEFAULT_ELEVATION),
            )
        for biome, (
            temperature,
            precipitation,
            elevation,
        ) in self._ELEVATION_ANCHORS.items():
            anchors[biome] = (
                float(temperature),
                float(precipitation),
                float(elevation),
            )
        return anchors

    def _build_water_anchors(self) -> dict[Biome, tuple[float, float, float, float]]:
        """Place each open-water biome at its (salinity, expanse, temp, depth) point."""
        return {
            biome: (float(salinity), float(expanse), float(temperature), float(depth))
            for biome, (
                salinity,
                expanse,
                temperature,
                depth,
            ) in self._AQUATIC_ANCHORS.items()
        }


BIOME_MATRIX = BiomeMatrix()
