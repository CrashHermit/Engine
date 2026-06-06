"""Biome names and climate × terrain mapping."""

from __future__ import annotations

from collections.abc import Iterable
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

    The surface is a 5x5x5 cube: temperature, precipitation, and elevation are
    each a five-band scale centred on its neutral default (mild, seasonal,
    midland), so the ordinary temperate lowland sits at the origin and every
    biome is a deviation outward. The climate grid anchors 25 biomes on the
    midland plane; four elevation biomes anchor higher up. Any surface point
    resolves to its nearest anchor, so band-centre inputs reproduce the grid
    while off-centre inputs fall to the closest neighbour. Shore, aquatic, and
    subterranean tiles branch out of the matrix before it is consulted.
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

    # The open-air elevation bands, low to high; elevation is the third axis,
    # centred on the midland default just as temperature centres on mild.
    _SURFACE_ELEVATIONS: tuple[Elevation, ...] = (
        Elevation.LOWLAND,
        Elevation.ROLLING,
        Elevation.MIDLAND,
        Elevation.HIGHLAND,
        Elevation.SUMMIT,
    )
    # The climate biomes anchor at this default elevation (the centre of the
    # axis); band-centre tiles here reproduce the climate grid exactly.
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

    _SUBTERRANEAN_GRID: dict[Elevation, Biome] = {
        Elevation.ABYSSAL: Biome.ABYSS,
        Elevation.BURIED: Biome.VAULT,
        Elevation.DEEP: Biome.DEEP_CAVERN,
        Elevation.LOW: Biome.CAVERN,
        Elevation.SHALLOW: Biome.CELLAR,
        Elevation.SUBGRADE: Biome.CRYPT,
    }

    def __init__(self) -> None:
        self._temperature_index = self._centered_index(Temperature)
        self._precipitation_index = self._centered_index(Precipitation)
        self._elevation_index = self._centered_index(self._SURFACE_ELEVATIONS)
        self._underground = frozenset(self._SUBTERRANEAN_GRID)
        self._anchors = self._build_anchors()

    @staticmethod
    def _centered_index[T](bands: Iterable[T]) -> dict[T, int]:
        """Map each ordered band to a coordinate centred on the middle band."""
        members = tuple(bands)
        centre = (len(members) - 1) // 2
        return {member: index - centre for index, member in enumerate(members)}

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
            return self._SHORE_GRID[hydrology]
        if hydrology != Hydrology.NONE:
            return self._aquatic_biome(hydrology, temperature, water_depth)
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
            float(self._elevation_index[elevation]),
        )

    def _surface_biome(
        self,
        temperature: Temperature,
        precipitation: Precipitation,
        elevation: Elevation,
    ) -> Biome:
        """Resolve the surface biome nearest to the climate-elevation point."""
        return self._nearest_anchor(self._anchor(temperature, precipitation, elevation))

    def _nearest_anchor(self, point: tuple[float, float, float]) -> Biome:
        temperature_value, precipitation_value, elevation_value = point
        return min(
            self._anchors,
            key=lambda biome: (
                (self._anchors[biome][0] - temperature_value) ** 2
                + (self._anchors[biome][1] - precipitation_value) ** 2
                + (self._anchors[biome][2] - elevation_value) ** 2
            ),
        )

    def _aquatic_biome(
        self,
        hydrology: Hydrology,
        temperature: Temperature,
        water_depth: WaterDepth,
    ) -> Biome:
        """Resolve the aquatic biome from the hydrology × temperature grid."""
        if water_depth == WaterDepth.SHALLOW:
            shallow = self._SHALLOW_SEA_GRID.get((hydrology, temperature))
            if shallow is not None:
                return shallow
        return self._AQUATIC_GRID[hydrology, temperature]


BIOME_MATRIX = BiomeMatrix()
