from __future__ import annotations



from dataclasses import dataclass

from enum import StrEnum





class Elevation(StrEnum):

    ABYSSAL = "abyssal"

    BURIED = "buried"

    DEEP = "deep"

    LOW = "low"

    SHALLOW = "shallow"

    SUBGRADE = "subgrade"

    LOWLAND = "lowland"

    BASIN = "basin"

    ROLLING = "rolling"

    MIDLAND = "midland"

    HIGHLAND = "highland"

    ALPINE = "alpine"

    SUMMIT = "summit"





ELEVATION: dict[Elevation, str] = {

    Elevation.ABYSSAL: "forgotten vaults; days from the surface",

    Elevation.BURIED: "deep caverns, far from sky",

    Elevation.DEEP: "mines, cisterns, established underworks",

    Elevation.LOW: "typical dungeon depth; sewers, undercroft",

    Elevation.SHALLOW: "cellars, basements, service tunnels",

    Elevation.SUBGRADE: "just below street level; crypts, sunken passages",

    Elevation.LOWLAND: "lowest open air; coast, docks, marshes, river bottoms",

    Elevation.BASIN: "sunken valley or bowl; sheltered below surroundings",

    Elevation.ROLLING: "gentle hills, foothills, sloped countryside",

    Elevation.MIDLAND: "typical settled elevation; anchor (like mild)",

    Elevation.HIGHLAND: "noticeably elevated; windier overlooks",

    Elevation.ALPINE: "harsh high slopes; thin air; snow line",

    Elevation.SUMMIT: "peak, aerie, exposed crown; nowhere higher",

}





class WaterForm(StrEnum):

    NONE = "none"

    STREAM = "stream"

    RIVER = "river"

    LAKE = "lake"

    SEA = "sea"

    OCEAN = "ocean"





WATER_FORM: dict[WaterForm, str] = {

    WaterForm.NONE: "dry land; no open water",

    WaterForm.STREAM: "brook, creek; wadeable; gentle flow",

    WaterForm.RIVER: "strong current; ford, bridge, or boat",

    WaterForm.LAKE: "standing water; shores, wind fetch",

    WaterForm.SEA: "nearshore open water; swell, spray, tides",

    WaterForm.OCEAN: "pelagic open water; deep; no land in sight",

}





class Salinity(StrEnum):

    FRESH = "fresh"

    BRACKISH = "brackish"

    SALT = "salt"





SALINITY: dict[Salinity, str] = {

    Salinity.FRESH: "drinkable; rivers, most lakes",

    Salinity.BRACKISH: "mixed; estuaries, tidal flats, lagoons",

    Salinity.SALT: "oceanic; seas, salt lakes",

}





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





_DEFAULT_SALINITY: dict[WaterForm, Salinity] = {

    WaterForm.NONE: Salinity.FRESH,

    WaterForm.STREAM: Salinity.FRESH,

    WaterForm.RIVER: Salinity.FRESH,

    WaterForm.LAKE: Salinity.FRESH,

    WaterForm.SEA: Salinity.SALT,

    WaterForm.OCEAN: Salinity.SALT,

}





def default_salinity(water_form: WaterForm) -> Salinity:
    """Return the usual salinity for a water form when none is specified."""
    return _DEFAULT_SALINITY[water_form]


def resolve_salinity(water_form: WaterForm, salinity: Salinity | None) -> Salinity:

    """Resolve salinity for aquatic tiles; ignored when ``water_form`` is ``NONE``."""

    if salinity is not None:

        return salinity

    return _DEFAULT_SALINITY[water_form]





@dataclass

class TerrainData:

    elevation: Elevation = Elevation.MIDLAND

    water_form: WaterForm = WaterForm.NONE

    salinity: Salinity | None = None

    water_depth: WaterDepth = WaterDepth.NONE

    coastal: bool = False



    @property

    def effective_salinity(self) -> Salinity:

        return resolve_salinity(self.water_form, self.salinity)

