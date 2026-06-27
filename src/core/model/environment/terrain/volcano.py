"""Volcano product entity and its morphology/activity enums."""

from dataclasses import dataclass
from enum import StrEnum


class VolcanoKind(StrEnum):
    """Volcano morphology, derived from its generating mechanism."""

    STRATO = "strato"  # subduction arc — steep composite cone
    SHIELD = "shield"  # hotspot — broad basaltic shield
    FISSURE = "fissure"  # rift / mid-ocean ridge — fissure eruption


class VolcanoStatus(StrEnum):
    """Present-day activity of a volcano."""

    ACTIVE = "active"
    DORMANT = "dormant"
    EXTINCT = "extinct"


@dataclass
class Volcano:
    """A discrete volcano.

    Built by the vulcanism stage; ships on ``WorldData.volcanoes`` and is the
    object the per-tile ``volcano_id`` column points back to.  ``cell`` is a mesh
    cell id during generation; the bake translates it to tile coordinates.
    """

    id: int  #: Unique volcano identifier (0-based; matches ``volcano_id``).
    cell: int  #: Summit location (mesh cell id pre-bake; tile coords post-bake).
    kind: VolcanoKind  #: Morphology (from mechanism).
    status: VolcanoStatus  #: Active / dormant / extinct.
    chain_id: int  #: Arc or hotspot trail grouping; ``-1`` = solitary.
    activity: float  #: [0,1] present-day activity at the summit.
    has_caldera: bool  #: Summit caldera forces a crater lake (set in VP2).
