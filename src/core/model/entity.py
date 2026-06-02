from enum import StrEnum


class Danger(StrEnum):
    """An entity's structural threat ceiling (NPCs carry danger, not HP). Maps
    to a magnitude cap in threat_envelope.py. The structured entity DTO lives in
    core/model/location.py (EntityData)."""

    LOW = "low"
    STANDARD = "standard"
    ELITE = "elite"
    DEADLY = "deadly"
