from __future__ import annotations

from dataclasses import dataclass, field

from src.core.model.environment.climate.biome import BiomeEnum


@dataclass
class BiomeWeights:
    biome: BiomeEnum
    weight: float


@dataclass
class BiomeCenter:
    biome: BiomeEnum
    ideal_temp: float
    ideal_precip: float


@dataclass
class LakeBasin:
    tiles: set[tuple[int, int]]
    spillway: tuple[int, int] | None


@dataclass
class RiverSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    flux: float


@dataclass
class MeshCell:
    id: int
    site: tuple[float, float]
    neighbors: list[int] = field(default_factory=list)
    landmass_id: int = -1
    is_land: bool = False
    landmass_class: int = 0  # 0=ocean 1=island 2=landmass 3=major
    coast_distance: float = 0.0
    z: float = 0.0
    temperature: float = 0.0
    precipitation: float = 0.0
    wind_u: float = 0.0
    wind_v: float = 0.0
    wind_magnitude: float = 0.0
    drainage: int = 0
    river_flux: float = 0.0
    is_lake: bool = False
    is_river: bool = False
    biome_weights: list[BiomeWeights] = field(default_factory=list)


@dataclass
class VoronoiMesh:
    width: float
    height: float
    cells: list[MeshCell] = field(default_factory=list)


@dataclass
class GridPositionData:
    x: int = 0
    y: int = 0
    landmass_id: int = -1
    is_land: bool = False
    landmass_class: int = 0
    coast_distance: float = 0.0
    z: float = 0.0
    temperature: float = 0.0
    precipitation: float = 0.0
    wind_u: float = 0.0
    wind_v: float = 0.0
    wind_magnitude: float = 0.0
    drainage_tiles: int = 0
    river_flux: float = 0.0
    is_lake: bool = False
    is_river: bool = False
    biome_weights: list[BiomeWeights] = field(default_factory=list)


@dataclass
class GridTileData:
    position: GridPositionData = field(default_factory=GridPositionData)
    neighbors: list[GridPositionData] = field(default_factory=list)


@dataclass
class WorldData:
    size: int = 100
    seed: int = 0
    mesh: VoronoiMesh | None = None
    grid: list[GridTileData] = field(default_factory=list)
    rivers: list[RiverSegment] = field(default_factory=list)
    landmass_sizes: dict[int, int] = field(default_factory=dict)
