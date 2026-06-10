from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.climate.biome import BiomeEnum
from src.core.model.environment.wind_intensity import WindIntensityBand


class ParticulateTypeEnum(StrEnum):
    NONE = "none"
    DUST = "dust"
    SAND = "sand"
    ASH = "ash"
    SMOKE = "smoke"
    SPORES = "spores"
    POLLEN = "pollen"


@dataclass(frozen=True)
class ParticulateTypeInfo:
    label: str
    description: str
    flavor: list[str]


INFO: dict[ParticulateTypeEnum, ParticulateTypeInfo] = {
    ParticulateTypeEnum.NONE: ParticulateTypeInfo(
        label="None",
        description="No airborne particulates of note.",
        flavor=[
            "Air reads clear at arm's length.",
            "Breathing stays easy.",
            "Distant objects stay sharp.",
            "Nothing grits the teeth.",
            "Surfaces stay clean in the wind.",
        ],
    ),
    ParticulateTypeEnum.DUST: ParticulateTypeInfo(
        label="Dust",
        description="Fine dry particles carried on the wind.",
        flavor=[
            "A dry taste coats the tongue.",
            "Sunbeams show floating motes.",
            "Cloth filters tan at the cuffs.",
            "Eyes water in gusts.",
            "Footfalls puff pale clouds.",
        ],
    ),
    ParticulateTypeEnum.SAND: ParticulateTypeInfo(
        label="Sand",
        description="Heavier grit scouring on the wind.",
        flavor=[
            "Granules rasp on skin.",
            "Visibility drops in gusts.",
            "Metal pits over seasons.",
            "Boots fill with grit.",
            "The air scratches with each breath.",
        ],
    ),
    ParticulateTypeEnum.ASH: ParticulateTypeInfo(
        label="Ash",
        description="Pale volcanic or burned residue aloft.",
        flavor=[
            "Grey film settles on everything.",
            "A mineral tang in the mouth.",
            "Leaves look powdered.",
            "Water turns murky in open bowls.",
            "Footprints mark dark on pale ground.",
        ],
    ),
    ParticulateTypeEnum.SMOKE: ParticulateTypeInfo(
        label="Smoke",
        description="Combustion haze drifting through the air.",
        flavor=[
            "Eyes sting without flame nearby.",
            "Scent of char on every gust.",
            "Sun shows as a dull coin.",
            "Breath catches in the throat.",
            "Ash flecks swirl in the haze.",
        ],
    ),
    ParticulateTypeEnum.SPORES: ParticulateTypeInfo(
        label="Spores",
        description="Biological drift from fungus or rot.",
        flavor=[
            "A damp mushroom smell.",
            "Mornings feel thick in the lungs.",
            "Woodland air tastes alive.",
            "Allergies stir without pollen.",
            "Green shadows seem to breathe.",
        ],
    ),
    ParticulateTypeEnum.POLLEN: ParticulateTypeInfo(
        label="Pollen",
        description="Seasonal plant dust thick in the air.",
        flavor=[
            "Yellow-green film on still water.",
            "Noses tickle constantly.",
            "Bees work the gusty lanes.",
            "Bright mornings feel itchy.",
            "Blossom scent rides every breeze.",
        ],
    ),
}

PARTICULATE_TYPE_GRID: dict[
    tuple[BiomeEnum, WindIntensityBand], ParticulateTypeEnum
] = {
        # -- ICE_SHEET ---------------------------------------------------
        (BiomeEnum.ICE_SHEET, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityBand.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityBand.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityBand.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_SHEET, WindIntensityBand.HURRICANE): ParticulateTypeEnum.NONE,
        # -- POLAR_DESERT ------------------------------------------------
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.BREEZY): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.GALE): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.STORM): ParticulateTypeEnum.SAND,
        (BiomeEnum.POLAR_DESERT, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SAND,
        # -- WINDFELL ----------------------------------------------------
        (BiomeEnum.WINDFELL, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WINDFELL, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.WINDFELL, WindIntensityBand.BREEZY): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityBand.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityBand.STORM): ParticulateTypeEnum.DUST,
        (BiomeEnum.WINDFELL, WindIntensityBand.HURRICANE): ParticulateTypeEnum.DUST,
        # -- FROST_BOG ---------------------------------------------------
        (BiomeEnum.FROST_BOG, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.FROST_BOG, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.FROST_BOG, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FROST_BOG, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- ICE_MIRE ----------------------------------------------------
        (BiomeEnum.ICE_MIRE, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityBand.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityBand.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityBand.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.ICE_MIRE, WindIntensityBand.HURRICANE): ParticulateTypeEnum.NONE,
        # -- GLACIAL_MARGIN ----------------------------------------------
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityBand.BREEZY): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.GLACIAL_MARGIN,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityBand.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.GLACIAL_MARGIN, WindIntensityBand.STORM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.GLACIAL_MARGIN,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.NONE,
        # -- MELTING_PACK ------------------------------------------------
        (BiomeEnum.MELTING_PACK, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityBand.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityBand.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityBand.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MELTING_PACK, WindIntensityBand.HURRICANE): ParticulateTypeEnum.NONE,
        # -- COLD_DESERT -------------------------------------------------
        (BiomeEnum.COLD_DESERT, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.COLD_DESERT, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.COLD_DESERT, WindIntensityBand.BREEZY): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityBand.GALE): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityBand.STORM): ParticulateTypeEnum.ASH,
        (BiomeEnum.COLD_DESERT, WindIntensityBand.HURRICANE): ParticulateTypeEnum.ASH,
        # -- DRY_TAIGA ---------------------------------------------------
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.BREEZY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.STORM): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_TAIGA, WindIntensityBand.HURRICANE): ParticulateTypeEnum.DUST,
        # -- LICHEN_WOODLAND ---------------------------------------------
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityBand.BREEZY): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LICHEN_WOODLAND,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityBand.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.LICHEN_WOODLAND, WindIntensityBand.STORM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LICHEN_WOODLAND,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.NONE,
        # -- OPEN_BOREAL -------------------------------------------------
        (BiomeEnum.OPEN_BOREAL, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.OPEN_BOREAL, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.OPEN_BOREAL, WindIntensityBand.BREEZY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.OPEN_BOREAL, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.OPEN_BOREAL, WindIntensityBand.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.OPEN_BOREAL, WindIntensityBand.STORM): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.OPEN_BOREAL,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- DENSE_TAIGA -------------------------------------------------
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.BREEZY): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.GALE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.STORM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DENSE_TAIGA, WindIntensityBand.HURRICANE): ParticulateTypeEnum.NONE,
        # -- WET_BOREAL --------------------------------------------------
        (BiomeEnum.WET_BOREAL, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WET_BOREAL, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.WET_BOREAL, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_BOREAL, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- MUSKEG_BOG --------------------------------------------------
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MUSKEG_BOG, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- SAGEBRUSH_STEPPE --------------------------------------------
        (BiomeEnum.SAGEBRUSH_STEPPE, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.DUST,
        (BiomeEnum.SAGEBRUSH_STEPPE, WindIntensityBand.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.SAGEBRUSH_STEPPE, WindIntensityBand.STORM): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SAGEBRUSH_STEPPE,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.DUST,
        # -- SHORTGRASS_PRAIRIE ------------------------------------------
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.DUST,
        (
            BiomeEnum.SHORTGRASS_PRAIRIE,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.DUST,
        # -- MIXED_PRAIRIE -----------------------------------------------
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityBand.BREEZY): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MIXED_PRAIRIE,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityBand.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MIXED_PRAIRIE, WindIntensityBand.STORM): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MIXED_PRAIRIE,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- DECIDUOUS_FOREST --------------------------------------------
        (BiomeEnum.DECIDUOUS_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.DECIDUOUS_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- MOIST_TEMPERATE_FOREST --------------------------------------
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_TEMPERATE_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- COOL_RAINFOREST ---------------------------------------------
        (BiomeEnum.COOL_RAINFOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.COOL_RAINFOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.COOL_RAINFOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.COOL_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- FEN_WETLAND -------------------------------------------------
        (BiomeEnum.FEN_WETLAND, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.FEN_WETLAND, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.FEN_WETLAND, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FEN_WETLAND, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FEN_WETLAND, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FEN_WETLAND, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.FEN_WETLAND,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- BADLANDS ----------------------------------------------------
        (BiomeEnum.BADLANDS, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.BADLANDS, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.BADLANDS, WindIntensityBand.BREEZY): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityBand.GALE): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityBand.STORM): ParticulateTypeEnum.SAND,
        (BiomeEnum.BADLANDS, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SAND,
        # -- CHAPARRAL ---------------------------------------------------
        (BiomeEnum.CHAPARRAL, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.CHAPARRAL, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.CHAPARRAL, WindIntensityBand.BREEZY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityBand.GALE): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityBand.STORM): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.CHAPARRAL, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SMOKE,
        # -- WOODLAND_SAVANNA --------------------------------------------
        (BiomeEnum.WOODLAND_SAVANNA, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.WOODLAND_SAVANNA,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- EVERGREEN_OAK_FOREST ----------------------------------------
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.EVERGREEN_OAK_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- LAUREL_FOREST -----------------------------------------------
        (BiomeEnum.LAUREL_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.LAUREL_FOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.LAUREL_FOREST, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LAUREL_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.LAUREL_FOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.LAUREL_FOREST, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LAUREL_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- TEMPERATE_RAINFOREST ----------------------------------------
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TEMPERATE_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- PEAT_MARSH --------------------------------------------------
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (BiomeEnum.PEAT_MARSH, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SPORES,
        # -- SEMI_ARID_SHRUBLAND -----------------------------------------
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SEMI_ARID_SHRUBLAND,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SMOKE,
        # -- THORN_SCRUB -------------------------------------------------
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.BREEZY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.GALE): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.STORM): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.THORN_SCRUB, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SMOKE,
        # -- DRY_FOREST --------------------------------------------------
        (BiomeEnum.DRY_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_FOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_FOREST, WindIntensityBand.BREEZY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityBand.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityBand.STORM): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.DRY_FOREST, WindIntensityBand.HURRICANE): ParticulateTypeEnum.POLLEN,
        # -- MARITIME_WOODLAND -------------------------------------------
        (BiomeEnum.MARITIME_WOODLAND, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MARITIME_WOODLAND,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- SUBTROPICAL_RAINFOREST --------------------------------------
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SUBTROPICAL_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- WARM_RAINFOREST ---------------------------------------------
        (BiomeEnum.WARM_RAINFOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WARM_RAINFOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WARM_RAINFOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WARM_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- SWAMP_FOREST ------------------------------------------------
        (BiomeEnum.SWAMP_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SWAMP_FOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.SWAMP_FOREST, WindIntensityBand.BREEZY): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SWAMP_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.SWAMP_FOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.SWAMP_FOREST, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SWAMP_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- SAND_DESERT -------------------------------------------------
        (BiomeEnum.SAND_DESERT, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAND_DESERT, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAND_DESERT, WindIntensityBand.BREEZY): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityBand.GALE): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityBand.STORM): ParticulateTypeEnum.SAND,
        (BiomeEnum.SAND_DESERT, WindIntensityBand.HURRICANE): ParticulateTypeEnum.SAND,
        # -- SAVANNA_SCRUB -----------------------------------------------
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityBand.BREEZY): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SAVANNA_SCRUB,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityBand.GALE): ParticulateTypeEnum.SMOKE,
        (BiomeEnum.SAVANNA_SCRUB, WindIntensityBand.STORM): ParticulateTypeEnum.SMOKE,
        (
            BiomeEnum.SAVANNA_SCRUB,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SMOKE,
        # -- SEASONAL_FOREST ---------------------------------------------
        (BiomeEnum.SEASONAL_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.SEASONAL_FOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.SEASONAL_FOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.SEASONAL_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- MONSOON_RAINFOREST ------------------------------------------
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- TROPICAL_RAINFOREST -----------------------------------------
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.TROPICAL_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- WET_RAINFOREST ----------------------------------------------
        (BiomeEnum.WET_RAINFOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.WET_RAINFOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.WET_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WET_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_RAINFOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.WET_RAINFOREST, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.WET_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- MANGROVE_SWAMP ----------------------------------------------
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MANGROVE_SWAMP,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MANGROVE_SWAMP,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MANGROVE_SWAMP, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MANGROVE_SWAMP,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- SCORCHING_WASTELAND -----------------------------------------
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SAND,
        (
            BiomeEnum.SCORCHING_WASTELAND,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SAND,
        # -- DRY_SAVANNA -------------------------------------------------
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.BREEZY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.BLUSTERY): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.GALE): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.STORM): ParticulateTypeEnum.DUST,
        (BiomeEnum.DRY_SAVANNA, WindIntensityBand.HURRICANE): ParticulateTypeEnum.DUST,
        # -- MONSOON_FOREST ----------------------------------------------
        (BiomeEnum.MONSOON_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MONSOON_FOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.MONSOON_FOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MONSOON_FOREST, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.MONSOON_FOREST, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.MONSOON_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- MOIST_FOREST ------------------------------------------------
        (BiomeEnum.MOIST_FOREST, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.MOIST_FOREST, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (BiomeEnum.MOIST_FOREST, WindIntensityBand.BREEZY): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_FOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MOIST_FOREST, WindIntensityBand.GALE): ParticulateTypeEnum.POLLEN,
        (BiomeEnum.MOIST_FOREST, WindIntensityBand.STORM): ParticulateTypeEnum.POLLEN,
        (
            BiomeEnum.MOIST_FOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.POLLEN,
        # -- LOWLAND_RAINFOREST ------------------------------------------
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.LOWLAND_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- EQUATORIAL_RAINFOREST ---------------------------------------
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.CALM,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.GENTLE,
        ): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.GALE,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.STORM,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.EQUATORIAL_RAINFOREST,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
        # -- FLOODED_JUNGLE ----------------------------------------------
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityBand.CALM): ParticulateTypeEnum.NONE,
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityBand.GENTLE): ParticulateTypeEnum.NONE,
        (
            BiomeEnum.FLOODED_JUNGLE,
            WindIntensityBand.BREEZY,
        ): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.FLOODED_JUNGLE,
            WindIntensityBand.BLUSTERY,
        ): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityBand.GALE): ParticulateTypeEnum.SPORES,
        (BiomeEnum.FLOODED_JUNGLE, WindIntensityBand.STORM): ParticulateTypeEnum.SPORES,
        (
            BiomeEnum.FLOODED_JUNGLE,
            WindIntensityBand.HURRICANE,
        ): ParticulateTypeEnum.SPORES,
    }
