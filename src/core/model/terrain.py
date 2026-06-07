from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class Elevation(IntEnum):
    LOWLAND = 0
    ROLLING = 1
    MIDLAND = 2
    HIGHLAND = 3
    SUMMIT = 4


ELEVATION: dict[Elevation, str] = {
    Elevation.LOWLAND: "lowest open air; coast, docks, marshes, river bottoms",
    Elevation.ROLLING: "gentle hills, foothills, sloped countryside",
    Elevation.MIDLAND: "typical settled elevation; anchor (like mild)",
    Elevation.HIGHLAND: "noticeably elevated; windier overlooks",
    Elevation.SUMMIT: "peak, aerie, exposed crown; nowhere higher",
}


class Depth(IntEnum):
    SUBGRADE = 0
    SHALLOW = 1
    LOW = 2
    DEEP = 3
    ABYSSAL = 4


DEPTH: dict[Depth, str] = {
    Depth.SUBGRADE: "just below street level; crypts, sunken passages",
    Depth.SHALLOW: "cellars, basements, service tunnels",
    Depth.LOW: "typical dungeon depth; sewers, undercroft",
    Depth.DEEP: "mines, cisterns, established underworks",
    Depth.ABYSSAL: "forgotten vaults; days from the surface",
}


class Hydrology(StrEnum):
    """Where land meets water: dry ground or a categorical shore landform.

    Open water is no longer modelled here — it is an ordinal medium (see
    ``WaterData``). This axis is for the land's relationship to the waterline,
    which is a shape, not a scale.
    """

    NONE = "none"
    BEACH = "beach"
    CLIFF = "cliff"
    HEADLAND = "headland"
    TIDAL_FLAT = "tidal_flat"


HYDROLOGY: dict[Hydrology, str] = {
    Hydrology.NONE: "dry land; no open water",
    Hydrology.BEACH: "sandy shore; dunes, surf line, gentle slope to the water",
    Hydrology.CLIFF: "sea cliff; dry rock face dropping to open water below",
    Hydrology.HEADLAND: "rocky promontory; headland jutting into open water",
    Hydrology.TIDAL_FLAT: "tidal flat; mud, salt marsh edge, channels at low tide",
}

SHORE_HYDROLOGY: frozenset[Hydrology] = frozenset(
    {
        Hydrology.BEACH,
        Hydrology.CLIFF,
        Hydrology.HEADLAND,
        Hydrology.TIDAL_FLAT,
    }
)


class Salinity(IntEnum):
    FRESH = 0
    BRACKISH = 2
    SALINE = 4


SALINITY: dict[Salinity, str] = {
    Salinity.FRESH: "freshwater; rivers, lakes, springs",
    Salinity.BRACKISH: "brackish; estuary mixing, salt marsh, tidal reach",
    Salinity.SALINE: "salt water; seas and open ocean",
}


class Expanse(IntEnum):
    CHANNEL = 0
    COURSE = 1
    BASIN = 2
    NEARSHORE = 3
    OPEN = 4


EXPANSE: dict[Expanse, str] = {
    Expanse.CHANNEL: "narrow flow; brook, creek, ditch",
    Expanse.COURSE: "broad flow; river current, no easy ford",
    Expanse.BASIN: "enclosed standing water; pond, lake, lagoon",
    Expanse.NEARSHORE: "coastal margin; bays and shallows within sight of land",
    Expanse.OPEN: "open water; pelagic reach, no land in sight",
}


class WaterDepth(IntEnum):
    NONE = 0
    SHALLOW = 1
    MODERATE = 2
    DEEP = 3
    VERY_DEEP = 4


WATER_DEPTH: dict[WaterDepth, str] = {
    WaterDepth.NONE: "dry land; no open water",
    WaterDepth.SHALLOW: "shallow; wadeable, sunlit bottom",
    WaterDepth.MODERATE: "moderate; over the head, bottom still near",
    WaterDepth.DEEP: "deep; dark below, no footing",
    WaterDepth.VERY_DEEP: "very deep; abyssal reach",
}


@dataclass
class WaterData:
    """An open body of water as a point on three ordinal axes.

    Salinity, expanse, and depth vary independently, so combinations the old
    named water bodies never spelled out (a warm shallow brackish lagoon) are
    expressible and resolve to their nearest known biome.
    """

    salinity: Salinity = Salinity.FRESH
    expanse: Expanse = Expanse.BASIN
    depth: WaterDepth = WaterDepth.MODERATE


@dataclass
class TerrainData:
    elevation: Elevation = Elevation.MIDLAND
    hydrology: Hydrology = Hydrology.NONE
    water: WaterData | None = None
    depth: Depth | None = None
