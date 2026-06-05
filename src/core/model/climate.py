from __future__ import annotations



from dataclasses import dataclass

from enum import StrEnum





class Temperature(StrEnum):

    FREEZING = "freezing"

    COOL = "cool"

    MILD = "mild"

    WARM = "warm"

    HOT = "hot"





TEMPERATURE: dict[Temperature, str] = {

    Temperature.FREEZING: "bitter cold; frigid wastes, polar night, breath clouds",

    Temperature.COOL: "brisk; light jacket; taiga edges, high-country spring",

    Temperature.MILD: "comfortable; anchor — temperate default",

    Temperature.WARM: "noticeably warm; lowland summer, savanna heat",

    Temperature.HOT: "oppressive heat; deserts, relentless sun, shade useless",

}





class Precipitation(StrEnum):

    ARID = "arid"

    DRY = "dry"

    SEASONAL = "seasonal"

    WET = "wet"

    DELUGE = "deluge"





GLOBAL_PRECIPITATION: dict[Precipitation, str] = {
    Precipitation.ARID: "desert dry; rain rare, brief, celebrated when it comes",
    Precipitation.DRY: "semi-arid; occasional showers; long clear spells",
    Precipitation.SEASONAL: "anchor — temperate norm; clear wet/dry rhythm",
    Precipitation.WET: "reliably rainy; green; frequent showers, long wet seasons",
    Precipitation.DELUGE: "relentless; rainforest, bog, near-perpetual rain",
}





@dataclass
class ClimateData:
    temperature: Temperature = Temperature.MILD
    precipitation: Precipitation = Precipitation.WET

