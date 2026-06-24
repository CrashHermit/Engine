"""Biome → landscape category: the coarse buckets biome-regions segment on.

The 49 fine biomes group into a handful of gameplay-legible landscapes ("a
forest", "the plains") so adjacent same-landscape biomes merge into one named
region.  Explicit (like ``BIOME_GRID``) rather than keyword-derived, because the
names mislead: ``polar_desert`` is tundra not desert, ``frost_bog`` is wetland
not tundra.  Each landscape is a :class:`~src.worldgen.features.RegionKind`.
"""

from src.core.model.environment.ecology.biome import BiomeEnum
from src.worldgen.features import RegionKind

# Display noun per landscape kind, used to name biome-regions ("Blackpine Forest").
LANDSCAPE_NOUN: dict[RegionKind, str] = {
    RegionKind.FOREST: "Forest",
    RegionKind.GRASSLAND: "Plains",
    RegionKind.DESERT: "Desert",
    RegionKind.TUNDRA: "Tundra",
    RegionKind.WETLAND: "Mire",
    RegionKind.SHRUBLAND: "Scrub",
}

# Deterministic iteration order for biome-region extraction (by RegionKind value).
LANDSCAPE_ORDER: tuple[RegionKind, ...] = (
    RegionKind.FOREST,
    RegionKind.GRASSLAND,
    RegionKind.DESERT,
    RegionKind.TUNDRA,
    RegionKind.WETLAND,
    RegionKind.SHRUBLAND,
)

LANDSCAPE_KIND: dict[BiomeEnum, RegionKind] = {
    # -- FRIGID --
    BiomeEnum.ICE_SHEET: RegionKind.TUNDRA,
    BiomeEnum.POLAR_DESERT: RegionKind.TUNDRA,
    BiomeEnum.WINDFELL: RegionKind.TUNDRA,
    BiomeEnum.FROST_BOG: RegionKind.WETLAND,
    BiomeEnum.ICE_MIRE: RegionKind.WETLAND,
    BiomeEnum.GLACIAL_MARGIN: RegionKind.TUNDRA,
    BiomeEnum.MELTING_PACK: RegionKind.TUNDRA,
    # -- FREEZING --
    BiomeEnum.COLD_DESERT: RegionKind.DESERT,
    BiomeEnum.DRY_TAIGA: RegionKind.FOREST,
    BiomeEnum.LICHEN_WOODLAND: RegionKind.FOREST,
    BiomeEnum.OPEN_BOREAL: RegionKind.FOREST,
    BiomeEnum.DENSE_TAIGA: RegionKind.FOREST,
    BiomeEnum.WET_BOREAL: RegionKind.FOREST,
    BiomeEnum.MUSKEG_BOG: RegionKind.WETLAND,
    # -- COOL --
    BiomeEnum.SAGEBRUSH_STEPPE: RegionKind.SHRUBLAND,
    BiomeEnum.SHORTGRASS_PRAIRIE: RegionKind.GRASSLAND,
    BiomeEnum.MIXED_PRAIRIE: RegionKind.GRASSLAND,
    BiomeEnum.DECIDUOUS_FOREST: RegionKind.FOREST,
    BiomeEnum.MOIST_TEMPERATE_FOREST: RegionKind.FOREST,
    BiomeEnum.COOL_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.FEN_WETLAND: RegionKind.WETLAND,
    # -- MILD --
    BiomeEnum.BADLANDS: RegionKind.DESERT,
    BiomeEnum.CHAPARRAL: RegionKind.SHRUBLAND,
    BiomeEnum.WOODLAND_SAVANNA: RegionKind.GRASSLAND,
    BiomeEnum.EVERGREEN_OAK_FOREST: RegionKind.FOREST,
    BiomeEnum.LAUREL_FOREST: RegionKind.FOREST,
    BiomeEnum.TEMPERATE_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.PEAT_MARSH: RegionKind.WETLAND,
    # -- WARM --
    BiomeEnum.SEMI_ARID_SHRUBLAND: RegionKind.SHRUBLAND,
    BiomeEnum.THORN_SCRUB: RegionKind.SHRUBLAND,
    BiomeEnum.DRY_FOREST: RegionKind.FOREST,
    BiomeEnum.MARITIME_WOODLAND: RegionKind.FOREST,
    BiomeEnum.SUBTROPICAL_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.WARM_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.SWAMP_FOREST: RegionKind.WETLAND,
    # -- HOT --
    BiomeEnum.SAND_DESERT: RegionKind.DESERT,
    BiomeEnum.SAVANNA_SCRUB: RegionKind.GRASSLAND,
    BiomeEnum.SEASONAL_FOREST: RegionKind.FOREST,
    BiomeEnum.MONSOON_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.TROPICAL_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.WET_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.MANGROVE_SWAMP: RegionKind.WETLAND,
    # -- SCORCHING --
    BiomeEnum.SCORCHING_WASTELAND: RegionKind.DESERT,
    BiomeEnum.DRY_SAVANNA: RegionKind.GRASSLAND,
    BiomeEnum.MONSOON_FOREST: RegionKind.FOREST,
    BiomeEnum.MOIST_FOREST: RegionKind.FOREST,
    BiomeEnum.LOWLAND_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.EQUATORIAL_RAINFOREST: RegionKind.FOREST,
    BiomeEnum.FLOODED_JUNGLE: RegionKind.WETLAND,
}
