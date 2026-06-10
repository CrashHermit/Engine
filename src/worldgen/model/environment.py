from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Terrain:
    """Solid-ground attributes: elevation and landmass classification."""

    # Surface elevation on a single continuous vertical axis where 0 == sea
    # level (set by SeaLevelStage and re-established by ErosionStage). Land is
    # > 0, ocean floor is < 0. The axis is unbounded, so it doubles as the
    # world's depth scale: sea depth at an ocean cell is -z, and underground
    # positions are simply z below this surface value.
    z: float = 0.0
    coast_distance: float = 0.0
    landmass_id: int = -1
    is_land: bool = False
    landmass_class: int = 0  # 0=ocean 1=island 2=landmass 3=major


@dataclass
class Climate:
    """Long-term climate attributes: temperature, precipitation, and wind."""

    temperature: float = 0.0
    precipitation: float = 0.0
    wind_u: float = 0.0
    wind_v: float = 0.0
    wind_magnitude: float = 0.0


@dataclass
class Hydrology:
    """Surface-water attributes: drainage, river flux, and water flags."""

    drainage: int = 0
    river_flux: float = 0.0
    is_lake: bool = False
    is_river: bool = False


@dataclass
class Ecology:
    """Living-world attributes. Biome is derived on demand from climate."""

    savagery: float = 0.0
    alignment: float = 0.0


@dataclass
class CellEnvironment:
    """The full per-cell attribute bundle, grouped by concern.

    Shared verbatim by both the Voronoi mesh (``MeshCell``) and the gameplay
    grid (``GridTile``) so a value is defined exactly once and the grid is a
    faithful rasterisation of the mesh. All values are raw, continuous
    generation outputs; banded enums and discrete biome are derived on demand
    by ``src.core.mechanic``.
    """

    terrain: Terrain = field(default_factory=Terrain)
    climate: Climate = field(default_factory=Climate)
    hydrology: Hydrology = field(default_factory=Hydrology)
    ecology: Ecology = field(default_factory=Ecology)
