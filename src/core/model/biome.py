"""Biome names and climate × terrain mapping."""

from __future__ import annotations

from enum import StrEnum

from src.core.model.climate import Precipitation, Temperature
from src.core.model.terrain import (
    Elevation,
    Salinity,
    WaterDepth,
    WaterForm,
    resolve_salinity,
)


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
    # ── Terrain overrides (elevation / coastal) ─────────────────────────────
    COASTAL = "coastal"
    MOOR = "moor"
    MONTANE_FOREST = "montane_forest"
    ALPINE_TUNDRA = "alpine_tundra"
    GLACIER = "glacier"
    # ── Aquatic overrides (water form × salinity) ───────────────────────────
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
    Biome.DESERT: "sand and stone; hot or warm aridity",
    Biome.SEMI_DESERT: "arid fringe; scrub and bare ground",
    Biome.SAVANNA: "grass with scattered trees; dry season",
    Biome.TROPICAL_WOODLAND: "open tropical trees; reliable rain",
    Biome.SEASONAL_JUNGLE: "wet-season dense growth; dry lull",
    Biome.DUNE_SEA: "hyper-arid dunes; relentless sun",
    Biome.THORN_SCRUB: "hot dry thornbelt; brutal heat",
    Biome.BUSHVELD: "hot grass-shrub; seasonal rhythm",
    Biome.MONSOON_FOREST: "burst-green canopy; heavy wet season",
    Biome.RAINFOREST: "dense equatorial canopy; constant moisture",
    Biome.COASTAL: "shore, salt spray, dunes, tidal flats",
    Biome.MOOR: "open high wet heath; wind, peat, low growth",
    Biome.MONTANE_FOREST: "mountain woods; cooler, steeper",
    Biome.ALPINE_TUNDRA: "above treeline; rock, snow, hardy mats",
    Biome.GLACIER: "permanent ice on peaks",
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


_SURFACE_BIOMES_TEMPERATURE_PRECIPITATION_GRID: dict[tuple[Temperature, Precipitation], Biome] = {
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
    (Temperature.WARM, Precipitation.ARID): Biome.DUNE_SEA,
    (Temperature.WARM, Precipitation.DRY): Biome.THORN_SCRUB,
    (Temperature.WARM, Precipitation.SEASONAL): Biome.BUSHVELD,
    (Temperature.WARM, Precipitation.WET): Biome.MONSOON_FOREST,
    (Temperature.WARM, Precipitation.DELUGE): Biome.RAINFOREST,
    (Temperature.HOT, Precipitation.ARID): Biome.DUNE_SEA,
    (Temperature.HOT, Precipitation.DRY): Biome.THORN_SCRUB,
    (Temperature.HOT, Precipitation.SEASONAL): Biome.BUSHVELD,
    (Temperature.HOT, Precipitation.WET): Biome.MONSOON_FOREST,
    (Temperature.HOT, Precipitation.DELUGE): Biome.RAINFOREST,
}

_SUBTERRANEAN_BIOMES_ELEVATION_GRID: dict[Elevation, Biome] = {
    Elevation.ABYSSAL: Biome.ABYSS,
    Elevation.BURIED: Biome.VAULT,
    Elevation.DEEP: Biome.DEEP_CAVERN,
    Elevation.LOW: Biome.CAVERN,
    Elevation.SHALLOW: Biome.CELLAR,
    Elevation.SUBGRADE: Biome.CRYPT,
}

_FOREST_BASES: frozenset[Biome] = frozenset(
    {
        Biome.TAIGA,
        Biome.BOREAL_FOREST,
        Biome.TEMPERATE_FOREST,
        Biome.TEMPERATE_RAINFOREST,
        Biome.TROPICAL_WOODLAND,
        Biome.SEASONAL_JUNGLE,
        Biome.MONSOON_FOREST,
        Biome.RAINFOREST,
    }
)
_WET_PRECIP: frozenset[Precipitation] = frozenset(
    {Precipitation.WET, Precipitation.DELUGE}
)
_COLD_TEMPS: frozenset[Temperature] = frozenset(
    {Temperature.FREEZING, Temperature.COOL}
)
_WARM_TEMPS: frozenset[Temperature] = frozenset(
    {Temperature.WARM, Temperature.HOT}
)
_SHALLOW_DEPTH: frozenset[WaterDepth] = frozenset({WaterDepth.SHALLOW})
_HIGH_ELEVATIONS: frozenset[Elevation] = frozenset(
    {Elevation.HIGHLAND, Elevation.ALPINE}
)
_PEAK_ELEVATIONS: frozenset[Elevation] = frozenset(
    {Elevation.ALPINE, Elevation.SUMMIT}
)
_UNDERGROUND: frozenset[Elevation] = frozenset(_SUBTERRANEAN_BIOMES_ELEVATION_GRID)


def biome_from(
    *,
    temperature: Temperature,
    precipitation: Precipitation,
    elevation: Elevation,
    water_form: WaterForm = WaterForm.NONE,
    salinity: Salinity | None = None,
    water_depth: WaterDepth = WaterDepth.NONE,
    coastal: bool = False,
) -> Biome:
    """Resolve the biome for a tile or location."""
    if water_form != WaterForm.NONE:
        return aquatic_override_biome(
            water_form=water_form,
            salinity=resolve_salinity(water_form, salinity),
            temperature=temperature,
            precipitation=precipitation,
            water_depth=water_depth,
        )
    if elevation in _UNDERGROUND:
        return get_subterranean_biome(elevation)
    base: Biome = get_surface_biome(temperature, precipitation)
    return elevation_override_surface_biome(
        base,
        elevation=elevation,
        coastal=coastal,
        temperature=temperature,
        precipitation=precipitation,
    )


def aquatic_override_biome(
    *,
    water_form: WaterForm,
    salinity: Salinity,
    temperature: Temperature,
    precipitation: Precipitation,
    water_depth: WaterDepth,
) -> Biome:
    """Apply aquatic overrides from water form and salinity, refined by climate."""
    if salinity == Salinity.BRACKISH:
        return Biome.ESTUARY

    if water_form == WaterForm.STREAM:
        return Biome.BROOK

    if water_form == WaterForm.RIVER:
        if salinity == Salinity.SALT:
            return Biome.ESTUARY
        if temperature == Temperature.FREEZING:
            return Biome.ICE_SHELF
        return Biome.RIVER

    if water_form == WaterForm.LAKE:
        if temperature == Temperature.FREEZING and salinity == Salinity.FRESH:
            return Biome.ICE_SHELF
        return Biome.LAKE

    if water_form in {WaterForm.SEA, WaterForm.OCEAN}:
        if salinity == Salinity.FRESH:
            return Biome.LAKE
        if temperature == Temperature.FREEZING:
            return Biome.POLAR_SEA
        if water_form == WaterForm.OCEAN:
            return Biome.OPEN_OCEAN
        if (
            water_depth in _SHALLOW_DEPTH
            and temperature in _COLD_TEMPS
            and precipitation in _WET_PRECIP
        ):
            return Biome.KELP_FOREST
        if (
            water_depth in _SHALLOW_DEPTH
            and temperature in _WARM_TEMPS
            and precipitation in _WET_PRECIP
        ):
            return Biome.CORAL_REEF
        return Biome.LITTORAL

    raise ValueError(f"unsupported water form: {water_form!r}")


def elevation_override_surface_biome(
    base: Biome,
    *,
    elevation: Elevation,
    coastal: bool,
    temperature: Temperature,
    precipitation: Precipitation,
) -> Biome:
    """Apply elevation and coastal overrides on top of the climate base biome."""
    if elevation == Elevation.SUMMIT and temperature == Temperature.FREEZING:
        return Biome.GLACIER

    if elevation in _PEAK_ELEVATIONS and temperature in _COLD_TEMPS:
        return Biome.ALPINE_TUNDRA

    if elevation in _HIGH_ELEVATIONS and base in _FOREST_BASES:
        return Biome.MONTANE_FOREST

    if (
        elevation == Elevation.HIGHLAND
        and temperature == Temperature.COOL
        and precipitation in _WET_PRECIP
        and base not in _FOREST_BASES
    ):
        return Biome.MOOR

    if coastal and elevation == Elevation.LOWLAND and precipitation in _WET_PRECIP:
        return Biome.COASTAL

    return base


def get_surface_biome(temperature: Temperature, precipitation: Precipitation) -> Biome:
    return _SURFACE_BIOMES_TEMPERATURE_PRECIPITATION_GRID[(temperature, precipitation)]


def get_subterranean_biome(elevation: Elevation) -> Biome:
    return _SUBTERRANEAN_BIOMES_ELEVATION_GRID[elevation]
