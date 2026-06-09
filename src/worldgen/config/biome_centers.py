from __future__ import annotations

from src.core.model.environment.climate.biome import BiomeEnum
from src.worldgen.data import BiomeCenter

BIOME_CENTERS: list[BiomeCenter] = [
    # ── FRIGID (0.0 to 0.15) ──────────────────────────────────────────────
    BiomeCenter(biome=BiomeEnum.ICE_SHEET, ideal_temp=0.00, ideal_precip=0.00),
    BiomeCenter(biome=BiomeEnum.POLAR_DESERT, ideal_temp=0.05, ideal_precip=0.10),
    BiomeCenter(biome=BiomeEnum.WINDFELL, ideal_temp=0.10, ideal_precip=0.25),
    BiomeCenter(biome=BiomeEnum.FROST_BOG, ideal_temp=0.05, ideal_precip=0.45),
    BiomeCenter(biome=BiomeEnum.ICE_MIRE, ideal_temp=0.10, ideal_precip=0.65),
    BiomeCenter(biome=BiomeEnum.GLACIAL_MARGIN, ideal_temp=0.05, ideal_precip=0.85),
    BiomeCenter(biome=BiomeEnum.MELTING_PACK, ideal_temp=0.10, ideal_precip=1.00),
    # ── FREEZING (0.15 to 0.3) ────────────────────────────────────────────
    BiomeCenter(biome=BiomeEnum.COLD_DESERT, ideal_temp=0.20, ideal_precip=0.05),
    BiomeCenter(biome=BiomeEnum.DRY_TAIGA, ideal_temp=0.25, ideal_precip=0.20),
    BiomeCenter(biome=BiomeEnum.LICHEN_WOODLAND, ideal_temp=0.20, ideal_precip=0.35),
    BiomeCenter(biome=BiomeEnum.OPEN_BOREAL, ideal_temp=0.28, ideal_precip=0.50),
    BiomeCenter(biome=BiomeEnum.DENSE_TAIGA, ideal_temp=0.22, ideal_precip=0.70),
    BiomeCenter(biome=BiomeEnum.WET_BOREAL, ideal_temp=0.28, ideal_precip=0.85),
    BiomeCenter(biome=BiomeEnum.MUSKEG_BOG, ideal_temp=0.25, ideal_precip=0.95),
    # ── COOL (0.3 to 0.45) ────────────────────────────────────────────────
    BiomeCenter(biome=BiomeEnum.SAGEBRUSH_STEPPE, ideal_temp=0.35, ideal_precip=0.08),
    BiomeCenter(biome=BiomeEnum.SHORTGRASS_PRAIRIE, ideal_temp=0.40, ideal_precip=0.22),
    BiomeCenter(biome=BiomeEnum.MIXED_PRAIRIE, ideal_temp=0.35, ideal_precip=0.38),
    BiomeCenter(biome=BiomeEnum.DECIDUOUS_FOREST, ideal_temp=0.42, ideal_precip=0.55),
    BiomeCenter(
        biome=BiomeEnum.MOIST_TEMPERATE_FOREST, ideal_temp=0.38, ideal_precip=0.75
    ),
    BiomeCenter(biome=BiomeEnum.COOL_RAINFOREST, ideal_temp=0.42, ideal_precip=0.90),
    BiomeCenter(biome=BiomeEnum.FEN_WETLAND, ideal_temp=0.38, ideal_precip=1.00),
    # ── MILD (0.45 to 0.6) ────────────────────────────────────────────────
    BiomeCenter(biome=BiomeEnum.BADLANDS, ideal_temp=0.55, ideal_precip=0.02),
    BiomeCenter(biome=BiomeEnum.CHAPARRAL, ideal_temp=0.50, ideal_precip=0.18),
    BiomeCenter(biome=BiomeEnum.WOODLAND_SAVANNA, ideal_temp=0.58, ideal_precip=0.35),
    BiomeCenter(
        biome=BiomeEnum.EVERGREEN_OAK_FOREST, ideal_temp=0.52, ideal_precip=0.55
    ),
    BiomeCenter(biome=BiomeEnum.LAUREL_FOREST, ideal_temp=0.58, ideal_precip=0.75),
    BiomeCenter(
        biome=BiomeEnum.TEMPERATE_RAINFOREST, ideal_temp=0.52, ideal_precip=0.92
    ),
    BiomeCenter(biome=BiomeEnum.PEAT_MARSH, ideal_temp=0.55, ideal_precip=1.00),
    # ── WARM (0.6 to 0.75) ────────────────────────────────────────────────
    BiomeCenter(
        biome=BiomeEnum.SEMI_ARID_SHRUBLAND, ideal_temp=0.70, ideal_precip=0.06
    ),
    BiomeCenter(biome=BiomeEnum.THORN_SCRUB, ideal_temp=0.65, ideal_precip=0.22),
    BiomeCenter(biome=BiomeEnum.DRY_FOREST, ideal_temp=0.72, ideal_precip=0.42),
    BiomeCenter(biome=BiomeEnum.MARITIME_WOODLAND, ideal_temp=0.68, ideal_precip=0.60),
    BiomeCenter(
        biome=BiomeEnum.SUBTROPICAL_RAINFOREST, ideal_temp=0.72, ideal_precip=0.82
    ),
    BiomeCenter(biome=BiomeEnum.WARM_RAINFOREST, ideal_temp=0.68, ideal_precip=0.95),
    BiomeCenter(biome=BiomeEnum.SWAMP_FOREST, ideal_temp=0.75, ideal_precip=1.00),
    # ── HOT (0.75 to 0.9) ─────────────────────────────────────────────────
    BiomeCenter(biome=BiomeEnum.SAND_DESERT, ideal_temp=0.85, ideal_precip=0.04),
    BiomeCenter(biome=BiomeEnum.SAVANNA_SCRUB, ideal_temp=0.80, ideal_precip=0.25),
    BiomeCenter(biome=BiomeEnum.SEASONAL_FOREST, ideal_temp=0.88, ideal_precip=0.48),
    BiomeCenter(biome=BiomeEnum.MONSOON_RAINFOREST, ideal_temp=0.82, ideal_precip=0.68),
    BiomeCenter(
        biome=BiomeEnum.TROPICAL_RAINFOREST, ideal_temp=0.88, ideal_precip=0.88
    ),
    BiomeCenter(biome=BiomeEnum.WET_RAINFOREST, ideal_temp=0.82, ideal_precip=0.96),
    BiomeCenter(biome=BiomeEnum.MANGROVE_SWAMP, ideal_temp=0.85, ideal_precip=1.00),
    # ── SCORCHING (0.9 to 1.0) ────────────────────────────────────────────
    BiomeCenter(
        biome=BiomeEnum.SCORCHING_WASTELAND, ideal_temp=0.98, ideal_precip=0.00
    ),
    BiomeCenter(biome=BiomeEnum.DRY_SAVANNA, ideal_temp=0.95, ideal_precip=0.20),
    BiomeCenter(biome=BiomeEnum.MONSOON_FOREST, ideal_temp=0.98, ideal_precip=0.45),
    BiomeCenter(biome=BiomeEnum.MOIST_FOREST, ideal_temp=0.95, ideal_precip=0.65),
    BiomeCenter(biome=BiomeEnum.LOWLAND_RAINFOREST, ideal_temp=0.98, ideal_precip=0.85),
    BiomeCenter(
        biome=BiomeEnum.EQUATORIAL_RAINFOREST, ideal_temp=0.95, ideal_precip=0.95
    ),
    BiomeCenter(biome=BiomeEnum.FLOODED_JUNGLE, ideal_temp=0.98, ideal_precip=1.00),
]
