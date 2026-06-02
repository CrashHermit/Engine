from enum import StrEnum
from dataclasses import dataclass

class Danger(StrEnum):
    LOW = "low"
    STANDARD = "standard"
    ELITE = "elite"
    DEADLY = "deadly"

@dataclass
class EntityData:
    name: str
    description: str
    scene_position: str
    danger: Danger = Danger.STANDARD
    scene_position: str = ""
    flavor: str = ""