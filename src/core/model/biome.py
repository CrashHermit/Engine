"""Biome names and climate × terrain mapping."""

from __future__ import annotations

from enum import StrEnum

from src.core.model.climate import Precipitation, Temperature
from src.core.model.terrain import SHORE_HYDROLOGY, Elevation, Hydrology, WaterDepth


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
    # ── Elevation biomes (high-altitude anchors) ─────────────────────────────
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
    # ── Underground (elevation below lowland) ───────────────────────────────
    ABYSS = "abyss"
    VAULT = "vault"
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
    Biome.VAULT: "buried deep works; far from sky",
    Biome.DEEP_CAVERN: "established deep halls; mines, cisterns",
    Biome.CAVERN: "typical underground; sewers, natural caves",
    Biome.CELLAR: "shallow underworks; basements, service tunnels",
    Biome.CRYPT: "subgrade; crypts, sunken passages near the street",
}


class BiomeMatrix:
    """Resolve biomes from climate and terrain via a nearest-anchor matrix.

    Surface biomes are points in (temperature, precipitation, altitude) space.
    The climate grid anchors 25 biomes at the midland default altitude; four
    elevation biomes anchor higher up. Any surface point resolves to its nearest
    anchor, so band-centre inputs reproduce the grid while off-centre inputs fall
    to the closest neighbour. Shore, aquatic, and subterranean tiles branch out
    of the matrix before it is consulted.
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

    # The open-air elevation bands, low to high; altitude is the third axis.
    _SURFACE_ELEVATIONS: tuple[Elevation, ...] = (
        Elevation.LOWLAND,
        Elevation.BASIN,
        Elevation.ROLLING,
        Elevation.MIDLAND,
        Elevation.HIGHLAND,
        Elevation.ALPINE,
        Elevation.SUMMIT,
    )
    # The climate biomes anchor at this default altitude; band-centre tiles here
    # reproduce the climate grid exactly.
    _DEFAULT_ELEVATION: Elevation = Elevation.MIDLAND

    # The four elevation biomes, anchored high in the matrix instead of resolved
    # by a separate override pass: (temperature, precipitation, altitude) centre.
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
            Elevation.ALPINE,
        ),
        Biome.GLACIER: (Temperature.FREEZING, Precipitation.SEASONAL, Elevation.SUMMIT),
    }

    _AQUATIC_GRID: dict[Hydrology, Biome] = {
        Hydrology.STREAM: Biome.BROOK,
        Hydrology.RIVER: Biome.RIVER,
        Hydrology.LAKE: Biome.LAKE,
        Hydrology.ESTUARY: Biome.ESTUARY,
        Hydrology.INLAND_SEA: Biome.LAKE,
        Hydrology.SEA: Biome.LITTORAL,
        Hydrology.OCEAN: Biome.OPEN_OCEAN,
    }

    _SHORE_GRID: dict[tuple[Hydrology, Elevation], Biome] = {
        (Hydrology.BEACH, Elevation.LOWLAND): Biome.BEACH,
        (Hydrology.BEACH, Elevation.BASIN): Biome.BEACH,
        (Hydrology.BEACH, Elevation.ROLLING): Biome.BEACH,
        (Hydrology.CLIFF, Elevation.LOWLAND): Biome.SEA_CLIFF,
        (Hydrology.CLIFF, Elevation.HIGHLAND): Biome.SEA_CLIFF,
        (Hydrology.CLIFF, Elevation.ALPINE): Biome.SEA_CLIFF,
        (Hydrology.CLIFF, Elevation.SUMMIT): Biome.SEA_CLIFF,
        (Hydrology.HEADLAND, Elevation.LOWLAND): Biome.HEADLAND,
        (Hydrology.HEADLAND, Elevation.ROLLING): Biome.HEADLAND,
        (Hydrology.HEADLAND, Elevation.HIGHLAND): Biome.HEADLAND,
        (Hydrology.TIDAL_FLAT, Elevation.LOWLAND): Biome.TIDAL_FLAT,
        (Hydrology.TIDAL_FLAT, Elevation.BASIN): Biome.TIDAL_FLAT,
    }

    _SUBTERRANEAN_GRID: dict[Elevation, Biome] = {
        Elevation.ABYSSAL: Biome.ABYSS,
        Elevation.BURIED: Biome.VAULT,
        Elevation.DEEP: Biome.DEEP_CAVERN,
        Elevation.LOW: Biome.CAVERN,
        Elevation.SHALLOW: Biome.CELLAR,
        Elevation.SUBGRADE: Biome.CRYPT,
    }

    # Climate / terrain bands used to refine salt and fresh water.
    _WET_PRECIP: frozenset[Precipitation] = frozenset(
        {Precipitation.WET, Precipitation.DELUGE}
    )
    _COLD_TEMPS: frozenset[Temperature] = frozenset(
        {Temperature.FREEZING, Temperature.COOL}
    )
    _WARM_TEMPS: frozenset[Temperature] = frozenset({Temperature.WARM, Temperature.HOT})
    _SHALLOW_DEPTH: frozenset[WaterDepth] = frozenset({WaterDepth.SHALLOW})
    _FRESHWATER_HYDROLOGY: frozenset[Hydrology] = frozenset(
        {Hydrology.RIVER, Hydrology.LAKE, Hydrology.INLAND_SEA}
    )
    _SALT_HYDROLOGY: frozenset[Hydrology] = frozenset({Hydrology.SEA, Hydrology.OCEAN})
    _DRY_LAND_HYDROLOGY: frozenset[Hydrology] = frozenset({Hydrology.NONE})

    def __init__(self) -> None:
        self._temperature_index = {
            temperature: index for index, temperature in enumerate(Temperature)
        }
        self._precipitation_index = {
            precipitation: index for index, precipitation in enumerate(Precipitation)
        }
        self._altitude_index = {
            elevation: index for index, elevation in enumerate(self._SURFACE_ELEVATIONS)
        }
        self._underground = frozenset(self._SUBTERRANEAN_GRID)
        self._anchors = self._build_anchors()

    def resolve(
        self,
        *,
        temperature: Temperature,
        precipitation: Precipitation,
        elevation: Elevation,
        hydrology: Hydrology = Hydrology.NONE,
        water_depth: WaterDepth = WaterDepth.NONE,
    ) -> Biome:
        """Resolve the biome for a tile or location."""
        if hydrology in SHORE_HYDROLOGY:
            return self._shore_biome(hydrology, elevation)
        if hydrology not in self._DRY_LAND_HYDROLOGY:
            return self._aquatic_biome(
                hydrology,
                temperature=temperature,
                precipitation=precipitation,
                water_depth=water_depth,
            )
        if elevation in self._underground:
            return self._SUBTERRANEAN_GRID[elevation]
        return self._surface_biome(temperature, precipitation, elevation)

    def _build_anchors(self) -> dict[Biome, tuple[float, float, float]]:
        anchors = {
            biome: self._anchor(temperature, precipitation, self._DEFAULT_ELEVATION)
            for (temperature, precipitation), biome in self._SURFACE_GRID.items()
        }
        for biome, (
            temperature,
            precipitation,
            elevation,
        ) in self._ELEVATION_ANCHORS.items():
            anchors[biome] = self._anchor(temperature, precipitation, elevation)
        return anchors

    def _anchor(
        self,
        temperature: Temperature,
        precipitation: Precipitation,
        elevation: Elevation,
    ) -> tuple[float, float, float]:
        return (
            float(self._temperature_index[temperature]),
            float(self._precipitation_index[precipitation]),
            float(self._altitude_index[elevation]),
        )

    def _surface_biome(
        self,
        temperature: Temperature,
        precipitation: Precipitation,
        elevation: Elevation,
    ) -> Biome:
        """Resolve the surface biome nearest to the climate-altitude point."""
        return self._nearest_anchor(self._anchor(temperature, precipitation, elevation))

    def _nearest_anchor(self, point: tuple[float, float, float]) -> Biome:
        temperature_value, precipitation_value, altitude_value = point
        return min(
            self._anchors,
            key=lambda biome: (
                (self._anchors[biome][0] - temperature_value) ** 2
                + (self._anchors[biome][1] - precipitation_value) ** 2
                + (self._anchors[biome][2] - altitude_value) ** 2
            ),
        )

    def _shore_biome(self, hydrology: Hydrology, elevation: Elevation) -> Biome:
        """Resolve the shore biome from the hydrology × elevation grid."""
        key = (hydrology, elevation)
        if key in self._SHORE_GRID:
            return self._SHORE_GRID[key]
        fallback = (hydrology, Elevation.LOWLAND)
        if fallback in self._SHORE_GRID:
            return self._SHORE_GRID[fallback]
        raise ValueError(f"unsupported shore hydrology and elevation: {key!r}")

    def _aquatic_biome(
        self,
        hydrology: Hydrology,
        *,
        temperature: Temperature,
        precipitation: Precipitation,
        water_depth: WaterDepth,
    ) -> Biome:
        """Resolve the aquatic biome from the hydrology grid, refined by climate."""
        if (
            hydrology in self._FRESHWATER_HYDROLOGY
            and temperature == Temperature.FREEZING
        ):
            return Biome.ICE_SHELF

        if hydrology in self._SALT_HYDROLOGY:
            if temperature == Temperature.FREEZING:
                return Biome.POLAR_SEA
            if hydrology == Hydrology.OCEAN:
                return Biome.OPEN_OCEAN
            if (
                water_depth in self._SHALLOW_DEPTH
                and temperature in self._COLD_TEMPS
                and precipitation in self._WET_PRECIP
            ):
                return Biome.KELP_FOREST
            if (
                water_depth in self._SHALLOW_DEPTH
                and temperature in self._WARM_TEMPS
                and precipitation in self._WET_PRECIP
            ):
                return Biome.CORAL_REEF
            return Biome.LITTORAL

        return self._AQUATIC_GRID[hydrology]


BIOME_MATRIX = BiomeMatrix()
