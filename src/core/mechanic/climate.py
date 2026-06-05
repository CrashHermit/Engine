from __future__ import annotations

from enum import StrEnum


class Temperature(StrEnum):
    FREEZING: str = "freezing"  # bitter cold; frigid wastes, polar night, breath clouds
    COOL: str = "cool"  # brisk; light jacket; taiga edges, high-country spring
    MILD: str = "mild"  # comfortable; anchor — temperate default
    WARM: str = "warm"  # noticeably warm; lowland summer, savanna heat
    HOT: str = "hot"  # oppressive heat; deserts, relentless sun, shade useless


class Precipitation(StrEnum):
    ARID: str = "arid"  # desert dry; rain rare, brief, celebrated when it comes
    DRY: str = "dry"  # semi-arid; occasional showers; long clear spells
    SEASONAL: str = "seasonal"  # anchor — temperate norm; clear wet/dry rhythm
    WET: str = "wet"  # reliably rainy; green; frequent showers, long wet seasons
    DELUGE: str = "deluge"  # relentless; rainforest, bog, near-perpetual rain
