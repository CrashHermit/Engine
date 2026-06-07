from __future__ import annotations

from enum import StrEnum

from src.core.model.environment.climate.precipitation import PrecipitationEnum
from src.core.model.environment.temperature import TemperatureEnum


class Biome(StrEnum):
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

    biome_grid: dict[tuple[TemperatureEnum, PrecipitationEnum], Biome] = {
        # ── FRIGID ────────────────────────────────────────────────────────────
        (TemperatureEnum.FRIGID, PrecipitationEnum.HYPER_ARID): Biome.ICE_SHEET,
        (TemperatureEnum.FRIGID, PrecipitationEnum.ARID): Biome.POLAR_DESERT,
        (TemperatureEnum.FRIGID, PrecipitationEnum.SEMI_ARID): Biome.WINDFELL,
        (TemperatureEnum.FRIGID, PrecipitationEnum.SUB_HUMID): Biome.FROST_BOG,
        (TemperatureEnum.FRIGID, PrecipitationEnum.HUMID): Biome.ICE_MIRE,
        (TemperatureEnum.FRIGID, PrecipitationEnum.HYPER_HUMID): Biome.GLACIAL_MARGIN,
        (TemperatureEnum.FRIGID, PrecipitationEnum.SATURATED): Biome.MELTING_PACK,
        # ── FREEZING ──────────────────────────────────────────────────────────
        (TemperatureEnum.FREEZING, PrecipitationEnum.HYPER_ARID): Biome.COLD_DESERT,
        (TemperatureEnum.FREEZING, PrecipitationEnum.ARID): Biome.DRY_TAIGA,
        (TemperatureEnum.FREEZING, PrecipitationEnum.SEMI_ARID): Biome.LICHEN_WOODLAND,
        (TemperatureEnum.FREEZING, PrecipitationEnum.SUB_HUMID): Biome.OPEN_BOREAL,
        (TemperatureEnum.FREEZING, PrecipitationEnum.HUMID): Biome.DENSE_TAIGA,
        (TemperatureEnum.FREEZING, PrecipitationEnum.HYPER_HUMID): Biome.WET_BOREAL,
        (TemperatureEnum.FREEZING, PrecipitationEnum.SATURATED): Biome.MUSKEG_BOG,
        # ── COOL ──────────────────────────────────────────────────────────────
        (TemperatureEnum.COOL, PrecipitationEnum.HYPER_ARID): Biome.SAGEBRUSH_STEPPE,
        (TemperatureEnum.COOL, PrecipitationEnum.ARID): Biome.SHORTGRASS_PRAIRIE,
        (TemperatureEnum.COOL, PrecipitationEnum.SEMI_ARID): Biome.MIXED_PRAIRIE,
        (TemperatureEnum.COOL, PrecipitationEnum.SUB_HUMID): Biome.DECIDUOUS_FOREST,
        (TemperatureEnum.COOL, PrecipitationEnum.HUMID): Biome.MOIST_TEMPERATE_FOREST,
        (TemperatureEnum.COOL, PrecipitationEnum.HYPER_HUMID): Biome.COOL_RAINFOREST,
        (TemperatureEnum.COOL, PrecipitationEnum.SATURATED): Biome.FEN_WETLAND,
        # ── MILD ──────────────────────────────────────────────────────────────
        (TemperatureEnum.MILD, PrecipitationEnum.HYPER_ARID): Biome.BADLANDS,
        (TemperatureEnum.MILD, PrecipitationEnum.ARID): Biome.CHAPARRAL,
        (TemperatureEnum.MILD, PrecipitationEnum.SEMI_ARID): Biome.WOODLAND_SAVANNA,
        (TemperatureEnum.MILD, PrecipitationEnum.SUB_HUMID): Biome.EVERGREEN_OAK_FOREST,
        (TemperatureEnum.MILD, PrecipitationEnum.HUMID): Biome.LAUREL_FOREST,
        (TemperatureEnum.MILD, PrecipitationEnum.HYPER_HUMID): Biome.TEMPERATE_RAINFOREST,
        (TemperatureEnum.MILD, PrecipitationEnum.SATURATED): Biome.PEAT_MARSH,
        # ── WARM ──────────────────────────────────────────────────────────────
        (TemperatureEnum.WARM, PrecipitationEnum.HYPER_ARID): Biome.SEMI_ARID_SHRUBLAND,
        (TemperatureEnum.WARM, PrecipitationEnum.ARID): Biome.THORN_SCRUB,
        (TemperatureEnum.WARM, PrecipitationEnum.SEMI_ARID): Biome.DRY_FOREST,
        (TemperatureEnum.WARM, PrecipitationEnum.SUB_HUMID): Biome.MARITIME_WOODLAND,
        (TemperatureEnum.WARM, PrecipitationEnum.HUMID): Biome.SUBTROPICAL_RAINFOREST,
        (TemperatureEnum.WARM, PrecipitationEnum.HYPER_HUMID): Biome.WARM_RAINFOREST,
        (TemperatureEnum.WARM, PrecipitationEnum.SATURATED): Biome.SWAMP_FOREST,
        # ── HOT ───────────────────────────────────────────────────────────────
        (TemperatureEnum.HOT, PrecipitationEnum.HYPER_ARID): Biome.SAND_DESERT,
        (TemperatureEnum.HOT, PrecipitationEnum.ARID): Biome.SAVANNA_SCRUB,
        (TemperatureEnum.HOT, PrecipitationEnum.SEMI_ARID): Biome.SEASONAL_FOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.SUB_HUMID): Biome.MONSOON_RAINFOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.HUMID): Biome.TROPICAL_RAINFOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.HYPER_HUMID): Biome.WET_RAINFOREST,
        (TemperatureEnum.HOT, PrecipitationEnum.SATURATED): Biome.MANGROVE_SWAMP,
        # ── SCORCHING ───────────────────────────────────────────────────────
        (TemperatureEnum.SCORCHING, PrecipitationEnum.HYPER_ARID): Biome.SCORCHING_WASTELAND,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.ARID): Biome.DRY_SAVANNA,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.SEMI_ARID): Biome.MONSOON_FOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.SUB_HUMID): Biome.MOIST_FOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.HUMID): Biome.LOWLAND_RAINFOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.HYPER_HUMID): Biome.EQUATORIAL_RAINFOREST,
        (TemperatureEnum.SCORCHING, PrecipitationEnum.SATURATED): Biome.FLOODED_JUNGLE,
    }

    def get_biome(
        self,
        temperature_enum: TemperatureEnum,
        precipitation_enum: PrecipitationEnum,
    ) -> Biome:
        return self.biome_grid[
            (temperature_enum, precipitation_enum)
        ]