from enum import StrEnum

from src.core.model.environment.climate.precipitation import PrecipitationBand
from src.core.model.environment.shared.temperature import TemperatureBand


class BiomeEnum(StrEnum):
    ICE_SHEET = "ice_sheet"
    POLAR_DESERT = "polar_desert"
    WINDFELL = "windfell"
    FROST_BOG = "frost_bog"
    ICE_MIRE = "ice_mire"
    GLACIAL_MARGIN = "glacial_margin"
    MELTING_PACK = "melting_pack"
    COLD_DESERT = "cold_desert"
    DRY_TAIGA = "dry_taiga"
    LICHEN_WOODLAND = "lichen_woodland"
    OPEN_BOREAL = "open_boreal"
    DENSE_TAIGA = "dense_taiga"
    WET_BOREAL = "wet_boreal"
    MUSKEG_BOG = "muskeg_bog"
    SAGEBRUSH_STEPPE = "sagebrush_steppe"
    SHORTGRASS_PRAIRIE = "shortgrass_prairie"
    MIXED_PRAIRIE = "mixed_prairie"
    DECIDUOUS_FOREST = "deciduous_forest"
    MOIST_TEMPERATE_FOREST = "moist_temperate_forest"
    COOL_RAINFOREST = "cool_rainforest"
    FEN_WETLAND = "fen_wetland"
    BADLANDS = "badlands"
    CHAPARRAL = "chaparral"
    WOODLAND_SAVANNA = "woodland_savanna"
    EVERGREEN_OAK_FOREST = "evergreen_oak_forest"
    LAUREL_FOREST = "laurel_forest"
    TEMPERATE_RAINFOREST = "temperate_rainforest"
    PEAT_MARSH = "peat_marsh"
    SEMI_ARID_SHRUBLAND = "semi_arid_shrubland"
    THORN_SCRUB = "thorn_scrub"
    DRY_FOREST = "dry_forest"
    MARITIME_WOODLAND = "maritime_woodland"
    SUBTROPICAL_RAINFOREST = "subtropical_rainforest"
    WARM_RAINFOREST = "warm_rainforest"
    SWAMP_FOREST = "swamp_forest"
    SAND_DESERT = "sand_desert"
    SAVANNA_SCRUB = "savanna_scrub"
    SEASONAL_FOREST = "seasonal_forest"
    MONSOON_RAINFOREST = "monsoon_rainforest"
    TROPICAL_RAINFOREST = "tropical_rainforest"
    WET_RAINFOREST = "wet_rainforest"
    MANGROVE_SWAMP = "mangrove_swamp"
    SCORCHING_WASTELAND = "scorching_wasteland"
    DRY_SAVANNA = "dry_savanna"
    MONSOON_FOREST = "monsoon_forest"
    MOIST_FOREST = "moist_forest"
    LOWLAND_RAINFOREST = "lowland_rainforest"
    EQUATORIAL_RAINFOREST = "equatorial_rainforest"
    FLOODED_JUNGLE = "flooded_jungle"


BIOME_GRID: dict[tuple[TemperatureBand, PrecipitationBand], BiomeEnum] = {
    # -- FRIGID --
    (TemperatureBand.FRIGID, PrecipitationBand.HYPER_ARID): BiomeEnum.ICE_SHEET,
    (TemperatureBand.FRIGID, PrecipitationBand.ARID): BiomeEnum.POLAR_DESERT,
    (TemperatureBand.FRIGID, PrecipitationBand.SEMI_ARID): BiomeEnum.WINDFELL,
    (TemperatureBand.FRIGID, PrecipitationBand.SUB_HUMID): BiomeEnum.FROST_BOG,
    (TemperatureBand.FRIGID, PrecipitationBand.HUMID): BiomeEnum.ICE_MIRE,
    (TemperatureBand.FRIGID, PrecipitationBand.HYPER_HUMID): BiomeEnum.GLACIAL_MARGIN,
    (TemperatureBand.FRIGID, PrecipitationBand.SATURATED): BiomeEnum.MELTING_PACK,
    # -- FREEZING --
    (TemperatureBand.FREEZING, PrecipitationBand.HYPER_ARID): BiomeEnum.COLD_DESERT,
    (TemperatureBand.FREEZING, PrecipitationBand.ARID): BiomeEnum.DRY_TAIGA,
    (TemperatureBand.FREEZING, PrecipitationBand.SEMI_ARID): BiomeEnum.LICHEN_WOODLAND,
    (TemperatureBand.FREEZING, PrecipitationBand.SUB_HUMID): BiomeEnum.OPEN_BOREAL,
    (TemperatureBand.FREEZING, PrecipitationBand.HUMID): BiomeEnum.DENSE_TAIGA,
    (TemperatureBand.FREEZING, PrecipitationBand.HYPER_HUMID): BiomeEnum.WET_BOREAL,
    (TemperatureBand.FREEZING, PrecipitationBand.SATURATED): BiomeEnum.MUSKEG_BOG,
    # -- COOL --
    (TemperatureBand.COOL, PrecipitationBand.HYPER_ARID): BiomeEnum.SAGEBRUSH_STEPPE,
    (TemperatureBand.COOL, PrecipitationBand.ARID): BiomeEnum.SHORTGRASS_PRAIRIE,
    (TemperatureBand.COOL, PrecipitationBand.SEMI_ARID): BiomeEnum.MIXED_PRAIRIE,
    (TemperatureBand.COOL, PrecipitationBand.SUB_HUMID): BiomeEnum.DECIDUOUS_FOREST,
    (TemperatureBand.COOL, PrecipitationBand.HUMID): BiomeEnum.MOIST_TEMPERATE_FOREST,
    (TemperatureBand.COOL, PrecipitationBand.HYPER_HUMID): BiomeEnum.COOL_RAINFOREST,
    (TemperatureBand.COOL, PrecipitationBand.SATURATED): BiomeEnum.FEN_WETLAND,
    # -- MILD --
    (TemperatureBand.MILD, PrecipitationBand.HYPER_ARID): BiomeEnum.BADLANDS,
    (TemperatureBand.MILD, PrecipitationBand.ARID): BiomeEnum.CHAPARRAL,
    (TemperatureBand.MILD, PrecipitationBand.SEMI_ARID): BiomeEnum.WOODLAND_SAVANNA,
    (TemperatureBand.MILD, PrecipitationBand.SUB_HUMID): BiomeEnum.EVERGREEN_OAK_FOREST,
    (TemperatureBand.MILD, PrecipitationBand.HUMID): BiomeEnum.LAUREL_FOREST,
    (
        TemperatureBand.MILD,
        PrecipitationBand.HYPER_HUMID,
    ): BiomeEnum.TEMPERATE_RAINFOREST,
    (TemperatureBand.MILD, PrecipitationBand.SATURATED): BiomeEnum.PEAT_MARSH,
    # -- WARM --
    (TemperatureBand.WARM, PrecipitationBand.HYPER_ARID): BiomeEnum.SEMI_ARID_SHRUBLAND,
    (TemperatureBand.WARM, PrecipitationBand.ARID): BiomeEnum.THORN_SCRUB,
    (TemperatureBand.WARM, PrecipitationBand.SEMI_ARID): BiomeEnum.DRY_FOREST,
    (TemperatureBand.WARM, PrecipitationBand.SUB_HUMID): BiomeEnum.MARITIME_WOODLAND,
    (TemperatureBand.WARM, PrecipitationBand.HUMID): BiomeEnum.SUBTROPICAL_RAINFOREST,
    (TemperatureBand.WARM, PrecipitationBand.HYPER_HUMID): BiomeEnum.WARM_RAINFOREST,
    (TemperatureBand.WARM, PrecipitationBand.SATURATED): BiomeEnum.SWAMP_FOREST,
    # -- HOT --
    (TemperatureBand.HOT, PrecipitationBand.HYPER_ARID): BiomeEnum.SAND_DESERT,
    (TemperatureBand.HOT, PrecipitationBand.ARID): BiomeEnum.SAVANNA_SCRUB,
    (TemperatureBand.HOT, PrecipitationBand.SEMI_ARID): BiomeEnum.SEASONAL_FOREST,
    (TemperatureBand.HOT, PrecipitationBand.SUB_HUMID): BiomeEnum.MONSOON_RAINFOREST,
    (TemperatureBand.HOT, PrecipitationBand.HUMID): BiomeEnum.TROPICAL_RAINFOREST,
    (TemperatureBand.HOT, PrecipitationBand.HYPER_HUMID): BiomeEnum.WET_RAINFOREST,
    (TemperatureBand.HOT, PrecipitationBand.SATURATED): BiomeEnum.MANGROVE_SWAMP,
    # -- SCORCHING --
    (
        TemperatureBand.SCORCHING,
        PrecipitationBand.HYPER_ARID,
    ): BiomeEnum.SCORCHING_WASTELAND,
    (TemperatureBand.SCORCHING, PrecipitationBand.ARID): BiomeEnum.DRY_SAVANNA,
    (TemperatureBand.SCORCHING, PrecipitationBand.SEMI_ARID): BiomeEnum.MONSOON_FOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.SUB_HUMID): BiomeEnum.MOIST_FOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.HUMID): BiomeEnum.LOWLAND_RAINFOREST,
    (
        TemperatureBand.SCORCHING,
        PrecipitationBand.HYPER_HUMID,
    ): BiomeEnum.EQUATORIAL_RAINFOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.SATURATED): BiomeEnum.FLOODED_JUNGLE,
}
