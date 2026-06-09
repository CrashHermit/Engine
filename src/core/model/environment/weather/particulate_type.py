from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.climate.biome import BiomeEnum
from src.core.model.environment.wind_intensity import WindIntensityEnum


class ParticulateTypeEnum(StrEnum):
    NONE = "none"
    DUST = "dust"
    SAND = "sand"
    ASH = "ash"
    SMOKE = "smoke"
    SPORES = "spores"
    POLLEN = "pollen"


@dataclass
class ParticulateTypeData:
    particulate_type: ParticulateTypeEnum


class ParticulateType:
    """Map biome and wind to airborne particulate matter."""

    particulate_type_grid: dict[
        tuple[BiomeEnum, WindIntensityEnum], ParticulateTypeEnum
    ] = {
        # -- ICE_SHEET ---------------------------------------------------
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.NONE,
        # -- POLAR_DESERT ------------------------------------------------
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.GALE): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.STORM): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SAND,
        # -- WINDFELL ----------------------------------------------------
        (BiomeEnum.WINDFELL, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WINDFELL, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.WINDFELL, WindIntensityEnum.BREEZY): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityEnum.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityEnum.STORM): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.DUST,
        # -- FROST_BOG ---------------------------------------------------
        (BiomeEnum.FROST_BOG, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.FROST_BOG, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.FROST_BOG, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- ICE_MIRE ----------------------------------------------------
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.NONE,
        # -- GLACIAL_MARGIN ----------------------------------------------
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityEnum.BREEZY): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.GLACIAL_MARGIN,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityEnum.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityEnum.STORM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.GLACIAL_MARGIN,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.NONE,
        # -- MELTING_PACK ------------------------------------------------
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.NONE,
        # -- COLD_DESERT -------------------------------------------------
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.BREEZY): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.GALE): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.STORM): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.ASH,
        # -- DRY_TAIGA ---------------------------------------------------
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.BREEZY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.STORM): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.DUST,
        # -- LICHEN_WOODLAND ---------------------------------------------
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityEnum.BREEZY): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LICHEN_WOODLAND,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityEnum.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityEnum.STORM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LICHEN_WOODLAND,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.NONE,
        # -- OPEN_BOREAL -------------------------------------------------
        (BiomeEnum.OPEN_BOREAL, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.OPEN_BOREAL, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.OPEN_BOREAL, WindIntensityEnum.BREEZY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.OPEN_BOREAL, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.OPEN_BOREAL, WindIntensityEnum.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.OPEN_BOREAL, WindIntensityEnum.STORM): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.OPEN_BOREAL,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- DENSE_TAIGA -------------------------------------------------
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.NONE,
        # -- WET_BOREAL --------------------------------------------------
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- MUSKEG_BOG --------------------------------------------------
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- SAGEBRUSH_STEPPE --------------------------------------------
        (BiomeEnum.SAGEBRUSH_STEPPE, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.DUST,
        (BiomeEnum.SAGEBRUSH_STEPPE, WindIntensityEnum.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.SAGEBRUSH_STEPPE, WindIntensityEnum.STORM): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.DUST,
        # -- SHORTGRASS_PRAIRIE ------------------------------------------
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.DUST,
        # -- MIXED_PRAIRIE -----------------------------------------------
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityEnum.BREEZY): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MIXED_PRAIRIE,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityEnum.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityEnum.STORM): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MIXED_PRAIRIE,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- DECIDUOUS_FOREST --------------------------------------------
        (BiomeEnum.DECIDUOUS_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- MOIST_TEMPERATE_FOREST --------------------------------------
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- COOL_RAINFOREST ---------------------------------------------
        (BiomeEnum.COOL_RAINFOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.COOL_RAINFOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.COOL_RAINFOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- FEN_WETLAND -------------------------------------------------
        (BiomeEnum.FEN_WETLAND, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.FEN_WETLAND, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.FEN_WETLAND, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FEN_WETLAND, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FEN_WETLAND, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FEN_WETLAND, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.FEN_WETLAND,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- BADLANDS ----------------------------------------------------
        (BiomeEnum.BADLANDS, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.BADLANDS, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.BADLANDS, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityEnum.GALE): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityEnum.STORM): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SAND,
        # -- CHAPARRAL ---------------------------------------------------
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.GALE): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.STORM): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SMOKE,
        # -- WOODLAND_SAVANNA --------------------------------------------
        (BiomeEnum.WOODLAND_SAVANNA, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- EVERGREEN_OAK_FOREST ----------------------------------------
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- LAUREL_FOREST -----------------------------------------------
        (BiomeEnum.LAUREL_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.LAUREL_FOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.LAUREL_FOREST, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LAUREL_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.LAUREL_FOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.LAUREL_FOREST, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LAUREL_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- TEMPERATE_RAINFOREST ----------------------------------------
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- PEAT_MARSH --------------------------------------------------
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- SEMI_ARID_SHRUBLAND -----------------------------------------
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SMOKE,
        # -- THORN_SCRUB -------------------------------------------------
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.GALE): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.STORM): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SMOKE,
        # -- DRY_FOREST --------------------------------------------------
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.BREEZY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.STORM): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.POLLEN,
        # -- MARITIME_WOODLAND -------------------------------------------
        (BiomeEnum.MARITIME_WOODLAND, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- SUBTROPICAL_RAINFOREST --------------------------------------
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- WARM_RAINFOREST ---------------------------------------------
        (BiomeEnum.WARM_RAINFOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WARM_RAINFOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WARM_RAINFOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- SWAMP_FOREST ------------------------------------------------
        (BiomeEnum.SWAMP_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SWAMP_FOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.SWAMP_FOREST, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SWAMP_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.SWAMP_FOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.SWAMP_FOREST, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SWAMP_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- SAND_DESERT -------------------------------------------------
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.GALE): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.STORM): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.SAND,
        # -- SAVANNA_SCRUB -----------------------------------------------
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityEnum.BREEZY): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SAVANNA_SCRUB,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityEnum.GALE): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityEnum.STORM): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SAVANNA_SCRUB,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SMOKE,
        # -- SEASONAL_FOREST ---------------------------------------------
        (BiomeEnum.SEASONAL_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SEASONAL_FOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.SEASONAL_FOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- MONSOON_RAINFOREST ------------------------------------------
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- TROPICAL_RAINFOREST -----------------------------------------
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- WET_RAINFOREST ----------------------------------------------
        (BiomeEnum.WET_RAINFOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WET_RAINFOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WET_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WET_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_RAINFOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_RAINFOREST, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WET_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- MANGROVE_SWAMP ----------------------------------------------
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MANGROVE_SWAMP,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MANGROVE_SWAMP,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MANGROVE_SWAMP,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- SCORCHING_WASTELAND -----------------------------------------
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SAND,
        # -- DRY_SAVANNA -------------------------------------------------
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.BREEZY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.BLUSTERY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.STORM): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityEnum.HURRICANE): ParticulateTypeEnum.DUST,
        # -- MONSOON_FOREST ----------------------------------------------
        (BiomeEnum.MONSOON_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MONSOON_FOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MONSOON_FOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MONSOON_FOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MONSOON_FOREST, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- MOIST_FOREST ------------------------------------------------
        (BiomeEnum.MOIST_FOREST, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MOIST_FOREST, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MOIST_FOREST, WindIntensityEnum.BREEZY): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_FOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MOIST_FOREST, WindIntensityEnum.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MOIST_FOREST, WindIntensityEnum.STORM): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_FOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- LOWLAND_RAINFOREST ------------------------------------------
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- EQUATORIAL_RAINFOREST ---------------------------------------
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- FLOODED_JUNGLE ----------------------------------------------
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityEnum.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityEnum.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.FLOODED_JUNGLE,
            WindIntensityEnum.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.FLOODED_JUNGLE,
            WindIntensityEnum.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityEnum.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityEnum.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.FLOODED_JUNGLE,
            WindIntensityEnum.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
    }

    def get_particulate_type(
        self,
        biome_enum: BiomeEnum,
        wind_intensity_enum: WindIntensityEnum,
    ) -> ParticulateTypeEnum:
        """Look up particulate type for a biome and wind pair."""
        return self.particulate_type_grid.get(
            (biome_enum, wind_intensity_enum), ParticulateTypeEnum.NONE
        )
