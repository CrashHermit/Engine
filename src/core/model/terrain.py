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
    NONE = "none"
    BEACH = "beach"
    CLIFF = "cliff"
    HEADLAND = "headland"
    TIDAL_FLAT = "tidal_flat"
    STREAM = "stream"
    RIVER = "river"
    LAKE = "lake"
    ESTUARY = "estuary"
    INLAND_SEA = "inland_sea"
    SEA = "sea"
    OCEAN = "ocean"


HYDROLOGY: dict[Hydrology, str] = {
    Hydrology.NONE: "dry land; no open water",
    Hydrology.BEACH: "sandy shore; dunes, surf line, gentle slope to the water",
    Hydrology.CLIFF: "sea cliff; dry rock face dropping to open water below",
    Hydrology.HEADLAND: "rocky promontory; headland jutting into open water",
    Hydrology.TIDAL_FLAT: "tidal flat; mud, salt marsh edge, channels at low tide",
    Hydrology.STREAM: "brook, creek; wadeable freshwater flow",
    Hydrology.RIVER: "strong current; ford, bridge, or boat; freshwater",
    Hydrology.LAKE: "standing freshwater; shores, wind fetch, waves",
    Hydrology.ESTUARY: "brackish tidal mix; mudflats, salt marsh edge",
    Hydrology.INLAND_SEA: "freshwater at ocean scale; Great Lakes, inland seas",
    Hydrology.SEA: "nearshore salt water; swell, spray, tides",
    Hydrology.OCEAN: "pelagic salt water; deep; no land in sight",
}

SHORE_HYDROLOGY: frozenset[Hydrology] = frozenset(
    {
        Hydrology.BEACH,
        Hydrology.CLIFF,
        Hydrology.HEADLAND,
        Hydrology.TIDAL_FLAT,
    }
)


class WaterDepth(StrEnum):
    NONE = "none"
    SHALLOW = "shallow"
    MODERATE = "moderate"
    DEEP = "deep"
    VERY_DEEP = "very_deep"


WATER_DEPTH: dict[WaterDepth, str] = {
    WaterDepth.NONE: "dry land; no open water",
    WaterDepth.SHALLOW: "shallow water; ankle deep",
    WaterDepth.MODERATE: "moderate water; waist deep",
    WaterDepth.DEEP: "deep water; head deep",
    WaterDepth.VERY_DEEP: "very deep water; neck deep",
}


@dataclass
class TerrainData:
    elevation: Elevation = Elevation.MIDLAND
    hydrology: Hydrology = Hydrology.NONE
    water_depth: WaterDepth = WaterDepth.NONE
    depth: Depth | None = None
