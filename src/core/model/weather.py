from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Humidity(StrEnum):
    ARID = "arid"
    DRY = "dry"
    CRISP = "crisp"
    MILD = "mild"
    HUMID = "humid"
    MUGGY = "muggy"
    SOAKING = "soaking"


HUMIDITY: dict[Humidity, str] = {
    Humidity.ARID: "bone-dry desert air; dust hangs; lips crack",
    Humidity.DRY: "noticeably dry air",
    Humidity.CRISP: "dry but fresh; sharp, clear air",
    Humidity.MILD: "comfortable, balanced; anchor (shared with temperature)",
    Humidity.HUMID: "moist air you can feel",
    Humidity.MUGGY: "sticky, heavy, oppressive",
    Humidity.SOAKING: "saturated air; monsoon-thick; rain-soaked world",
}


class Precipitation(StrEnum):
    NONE = "none"
    DRIZZLE = "drizzle"
    LIGHT = "light"
    STEADY = "steady"
    HEAVY = "heavy"
    TORRENTIAL = "torrential"
    CLOUDBURST = "cloudburst"


PRECIPITATION: dict[Precipitation, str] = {
    Precipitation.NONE: "dry sky; nothing falling",
    Precipitation.DRIZZLE: "fine mist; speckled ground; no puddles yet",
    Precipitation.LIGHT: "soft fall; umbrella optional; damp not soaked",
    Precipitation.STEADY: "ongoing; puddles form; cover within minutes",
    Precipitation.HEAVY: "hard fall; soaked fast; visibility suffers",
    Precipitation.TORRENTIAL: "sheets; roaring runoff; stay under cover",
    Precipitation.CLOUDBURST: "sudden, intense rain; visibility zero",
}


class WindDirection(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTH_EAST = "north_east"
    NORTH_WEST = "north_west"
    SOUTH_EAST = "south_east"
    SOUTH_WEST = "south_west"


WIND_DIRECTION: dict[WindDirection, str] = {
    WindDirection.NORTH: "wind from the north",
    WindDirection.SOUTH: "wind from the south",
    WindDirection.EAST: "wind from the east",
    WindDirection.WEST: "wind from the west",
    WindDirection.NORTH_EAST: "wind from the northeast",
    WindDirection.NORTH_WEST: "wind from the northwest",
    WindDirection.SOUTH_EAST: "wind from the southeast",
    WindDirection.SOUTH_WEST: "wind from the southwest",
}


class WindSpeed(StrEnum):
    CALM = "calm"
    GENTLE = "gentle"
    BREEZY = "breezy"
    BLUSTERY = "blustery"
    GALE = "gale"
    STORM = "storm"
    HURRICANE = "hurricane"


WIND_SPEED: dict[WindSpeed, str] = {
    WindSpeed.CALM: "still air; smoke rises straight",
    WindSpeed.GENTLE: "soft stir; leaves whisper, hair moves",
    WindSpeed.BREEZY: "steady push; flags snap, hair won't stay put",
    WindSpeed.BLUSTERY: "hard going; lean in, doors catch, umbrellas fail",
    WindSpeed.GALE: "sustained force; branches snap, hard to stand",
    WindSpeed.STORM: "storm-force; debris flies, travel dangerous",
    WindSpeed.HURRICANE: "catastrophic; shelter or perish",
}


class Temperature(StrEnum):
    FRIGID = "frigid"
    FREEZING = "freezing"
    COOL = "cool"
    MILD = "mild"
    WARM = "warm"
    HOT = "hot"
    SCORCHING = "scorching"


WEATHER_TEMPERATURE: dict[Temperature, str] = {
    Temperature.FRIGID: "lethal cold; flesh freezes; ice-bound, lifeless",
    Temperature.FREEZING: "bitter cold; polar night, breath clouds",
    Temperature.COOL: "brisk; light jacket; taiga edges, high-country spring",
    Temperature.MILD: "comfortable; anchor — temperate default",
    Temperature.WARM: "noticeably warm; lowland summer, savanna heat",
    Temperature.HOT: "oppressive heat; deserts, relentless sun",
    Temperature.SCORCHING: "furnace heat; shade useless; water vanishes",
}


@dataclass
class WeatherData:
    humidity: Humidity
    precipitation: Precipitation
    wind_direction: WindDirection
    wind_speed: WindSpeed
