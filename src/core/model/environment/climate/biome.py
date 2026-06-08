from __future__ import annotations

from enum import StrEnum

from src.core.model.environment.climate.precipitation import PrecipitationEnum
from src.core.model.environment.temperature import TemperatureEnum


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


class Biome:
    """Turn climate TemperatureEnum and precipitation into a biome."""

    biome_grid: dict[tuple[TemperatureEnum, PrecipitationEnum], BiomeEnum] = {
        # ── FRIGID ────────────────────────────────────────────────────────────
        (TemperatureEnum.FRIGID, PrecipitationEnum.HYPER_ARID): BiomeEnum.ICE_SHEET,
        (TemperatureEnum.FRIGID, PrecipitationEnum.ARID): BiomeEnum.POLAR_DESERT,
        (TemperatureEnum.FRIGID, PrecipitationEnum.SEMI_ARID): BiomeEnum.WINDFELL,
        (TemperatureEnum.FRIGID, PrecipitationEnum.SUB_HUMID): BiomeEnum.FROST_BOG,
        (TemperatureEnum.FRIGID, PrecipitationEnum.HUMID): BiomeEnum.ICE_MIRE,
        (TemperatureEnum.FRIGID, PrecipitationEnum.HYPER_HUMID): BiomeEnum.GLACIAL_MARGIN,
        (TemperatureEnum.FRIGID, PrecipitationEnum.SATURATED): BiomeEnum.MELTING_PACK,
        # ── FREEZING ──────────────────────────────────────────────────────────
        (TemperatureEnum.FREEZING, PrecipitationEnum.HYPER_ARID): BiomeEnum.COLD_DESERT,
        (TemperatureEnum.FREEZING, PrecipitationEnum.ARID): BiomeEnum.DRY_TAIGA,
        (TemperatureEnum.FREEZING, PrecipitationEnum.SEMI_ARID): BiomeEnum.LICHEN_WOODLAND,
        (TemperatureEnum.FREEZING, PrecipitationEnum.SUB_HUMID): BiomeEnum.OPEN_BOREAL,
        (TemperatureEnum.FREEZING, PrecipitationEnum.HUMID): BiomeEnum.DENSE_TAIGA,
        (TemperatureEnum.FREEZING, PrecipitationEnum.HYPER_HUMID): BiomeEnum.WET_BOREAL,
        (TemperatureEnum.FREEZING, PrecipitationEnum.SATURATED): BiomeEnum.MUSKEG_BOG,
        # ── COOL ──────────────────────────────────────────────────────────────
        (TemperatureEnum.COOL, PrecipitationEnum.HYPER_ARID): BiomeEnum.SAGEBRUSH_STEPPE,
        (TemperatureEnum.COOL, PrecipitationEnum.ARID): BiomeEnum.SHORTGRASS_PRAIRIE,
        (TemperatureEnum.COOL, PrecipitationEnum.SEMI_ARID): BiomeEnum.MIXED_PRAIRIE,
        (TemperatureEnum.COOL, PrecipitationEnum.SUB_HUMID): BiomeEnum.DECIDUOUS_FOREST,
        (TemperatureEnum.COOL, PrecipitationEnum.HUMID): BiomeEnum.MOIST_TEMPERATE_FOREST,
        (TemperatureEnum.COOL, PrecipitationEnum.HYPER_HUMID): BiomeEnum.COOL_RAINFOREST,
        (TemperatureEnum.COOL, PrecipitationEnum.SATURATED): BiomeEnum.FEN_WETLAND,
        # ── MILD ──────────────────────────────────────────────────────────────
        (TemperatureEnum.MILD, PrecipitationEnum.HYPER_ARID): BiomeEnum.BADLANDS,
        (TemperatureEnum.MILD, PrecipitationEnum.ARID): BiomeEnum.CHAPARRAL,
        (TemperatureEnum.MILD, PrecipitationEnum.SEMI_ARID): BiomeEnum.WOODLAND_SAVANNA,
        (TemperatureEnum.MILD, PrecipitationEnum.SUB_HUMID): BiomeEnum.EVERGREEN_OAK_FOREST,
        (TemperatureEnum.MILD, PrecipitationEnum.HUMID): BiomeEnum.LAUREL_FOREST,
        (TemperatureEnum.MILD, PrecipitationEnum.HYPER_HUMID): BiomeEnum.TEMPERATE_RAINFOREST,
        (TemperatureEnum.MILD, PrecipitationEnum.SATURATED): BiomeEnum.PEAT_MARSH,
        # ── WARM ──────────────────────────────────────────────────────────────
        (TemperatureEnum.WARM, PrecipitationEnum.HYPER_ARID): BiomeEnum.SEMI_ARID_SHRUBLAND,
        (TemperatureEnum.WARM, PrecipitationEnum.ARID): BiomeEnum.THORN_SCRUB,
        (TemperatureEnum.WARM, PrecipitationEnum.SEMI_ARID): BiomeEnum.DRY_FOREST,
        (TemperatureEnum.WARM, PrecipitationEnum.SUB_HUMID): BiomeEnum.MARITIME_WOODLAND,
        (TemperatureEnum.WARM, PrecipitationEnum.HUMID): BiomeEnum.SUBTROPICAL_RAINFOREST,
        (TemperatureEnum.WARM, PrecipitationEnum.HYPER_HUMID): BiomeEnum.WARM_RAINFOREST,
        (TemperatureEnum.WARM, PrecipitationEnum.SATURATED): BiomeEnum.SWAMP_FOREST,
        # ── HOT ───────────────────────────────────────────────────────────────
        (TemperatureEnum.HOT, PrecipitationEnum.HYPER_ARID): BiomeEnum.SAND_DESERT,
        (TemperatureEnum.HOT, PrecipitationEnum.ARID): BiomeEnum.SAVANNA_SCRUB,
        (TemperatureEnum.HOT, PrecipitationEnum.SEMI_ARID): BiomeEnum.SEASONAL_FOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.SUB_HUMID): BiomeEnum.MONSOON_RAINFOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.HUMID): BiomeEnum.TROPICAL_RAINFOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.HYPER_HUMID): BiomeEnum.WET_RAINFOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.SATURATED): BiomeEnum.MANGROVE_SWAMP,
        # ── SCORCHING ───────────────────────────────────────────────────────
        (TemperatureEnum.SCORCHING, PrecipitationEnum.HYPER_ARID): BiomeEnum.SCORCHING_WASTELAND,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.ARID): BiomeEnum.DRY_SAVANNA,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.SEMI_ARID): BiomeEnum.MONSOON_FOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.SUB_HUMID): BiomeEnum.MOIST_FOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.HUMID): BiomeEnum.LOWLAND_RAINFOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.HYPER_HUMID): BiomeEnum.EQUATORIAL_RAINFOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.SATURATED): BiomeEnum.FLOODED_JUNGLE,
    }

    def get_biome(
        self,
        temperature_enum: TemperatureEnum,
        precipitation_enum: PrecipitationEnum,
    ) -> BiomeEnum:
        return self.biome_grid[
            (temperature_enum, precipitation_enum)
        ]