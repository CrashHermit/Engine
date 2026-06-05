from __future__ import annotations

from enum import StrEnum


class Elevation(StrEnum):
    # Underground (enclosed; no open sky) — ordered deepest to nearest daylight
    ABYSSAL: str = "abyssal"  # forgotten vaults; days from the surface
    BURIED: str = "buried"  # deep caverns, far from sky
    DEEP: str = "deep"  # mines, cisterns, established underworks
    LOW: str = "low"  # typical dungeon depth; sewers, undercroft
    SHALLOW: str = "shallow"  # cellars, basements, service tunnels
    SUBGRADE: str = "subgrade"  # just below street level; crypts, sunken passages
    # Surface (open air) — lowland is the seam between subgrade and open sky
    LOWLAND: str = "lowland"  # lowest open air; coast, docks, marshes, river bottoms
    BASIN: str = "basin"  # sunken valley or bowl; sheltered below surroundings
    ROLLING: str = "rolling"  # gentle hills, foothills, sloped countryside
    MIDLAND: str = "midland"  # typical settled elevation; anchor (like mild)
    HIGHLAND: str = "highland"  # noticeably elevated; windier overlooks
    ALPINE: str = "alpine"  # harsh high slopes; thin air; snow line
    SUMMIT: str = "summit"  # peak, aerie, exposed crown; nowhere higher
