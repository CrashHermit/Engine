"""Biome names and climate × terrain mapping."""

from __future__ import annotations

from enum import StrEnum

from src.core.mechanic.climate import Precipitation, Temperature
from src.core.mechanic.terrain import Elevation


class Biome(StrEnum):
    # ── Climate grid (5×5: temperature × precipitation) ───────────────────
    # freezing
    POLAR_DESERT: str = "polar_desert"  # ice and bare rock; hyper-arid cold
    POLAR_BARRENS: str = "polar_barrens"  # frozen wasteland; dry wind, no snowpack
    TUNDRA: str = "tundra"  # permafrost, moss, dwarf shrubs
    SNOWY_TUNDRA: str = "snowy_tundra"  # persistent snow; brief thaw
    FEN: str = "fen"  # cold sodden flats; seasonal ice and standing water
    # cool
    COLD_DESERT: str = "cold_desert"  # high cold barrens; dry, sparse life
    STEPPE: str = "steppe"  # open continental grass; hard winters
    TAIGA: str = "taiga"  # boreal conifer belt; long cold season
    BOREAL_FOREST: str = "boreal_forest"  # wet boreal woods; snow-heavy
    BOG: str = "bog"  # peat mire; cold, acid, sodden
    # mild
    SCRUBLAND: str = "scrubland"  # dry shrubs, chaparral, thornbrush
    PRAIRIE: str = "prairie"  # open temperate grass; few trees
    TEMPERATE_FOREST: str = "temperate_forest"  # deciduous/mixed woods; four seasons
    TEMPERATE_RAINFOREST: str = "temperate_rainforest"  # wet mild woods; year-round green
    MARSH: str = "marsh"  # reedbeds, warm standing water
    # warm
    DESERT: str = "desert"  # sand and stone; hot or warm aridity
    SEMI_DESERT: str = "semi_desert"  # arid fringe; scrub and bare ground
    SAVANNA: str = "savanna"  # grass with scattered trees; dry season
    TROPICAL_WOODLAND: str = "tropical_woodland"  # open tropical trees; reliable rain
    SEASONAL_JUNGLE: str = "seasonal_jungle"  # wet-season dense growth; dry lull
    # hot
    DUNE_SEA: str = "dune_sea"  # hyper-arid dunes; relentless sun
    THORN_SCRUB: str = "thorn_scrub"  # hot dry thornbelt; brutal heat
    BUSHVELD: str = "bushveld"  # hot grass-shrub; seasonal rhythm
    MONSOON_FOREST: str = "monsoon_forest"  # burst-green canopy; heavy wet season
    RAINFOREST: str = "rainforest"  # dense equatorial canopy; constant moisture

    # ── Terrain overrides (elevation / coastal) ─────────────────────────────
    COASTAL: str = "coastal"  # shore, salt spray, dunes, tidal flats
    MOOR: str = "moor"  # open high wet heath; wind, peat, low growth
    MONTANE_FOREST: str = "montane_forest"  # mountain woods; cooler, steeper
    ALPINE_TUNDRA: str = "alpine_tundra"  # above treeline; rock, snow, hardy mats
    GLACIER: str = "glacier"  # permanent ice on peaks

    # ── Underground (elevation below lowland) ───────────────────────────────
    ABYSS: str = "abyss"  # abyssal vaults; days from daylight
    VAULT: str = "vault"  # buried deep works; far from sky
    DEEP_CAVERN: str = "deep_cavern"  # established deep halls; mines, cisterns
    CAVERN: str = "cavern"  # typical underground; sewers, natural caves
    CELLAR: str = "cellar"  # shallow underworks; basements, service tunnels
    CRYPT: str = "crypt"  # subgrade; crypts, sunken passages near the street



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
    coastal: bool = False,
) -> Biome:
    """Resolve the biome for a tile or location."""
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

