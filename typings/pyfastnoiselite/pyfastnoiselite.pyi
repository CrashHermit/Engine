from enum import Enum

import numpy as np
from numpy.typing import NDArray

__author__: str
__license__: str
__version__: str
__copyright__: str

class NoiseType(Enum):
    NoiseType_OpenSimplex2: NoiseType
    NoiseType_OpenSimplex2S: NoiseType
    NoiseType_Cellular: NoiseType
    NoiseType_Perlin: NoiseType
    NoiseType_ValueCubic: NoiseType
    NoiseType_Value: NoiseType

class RotationType3D(Enum):
    RotationType3D_None: RotationType3D
    RotationType3D_ImproveXYPlanes: RotationType3D
    RotationType3D_ImproveXZPlanes: RotationType3D

class FractalType(Enum):
    FractalType_None: FractalType
    FractalType_FBm: FractalType
    FractalType_Ridged: FractalType
    FractalType_PingPong: FractalType
    FractalType_DomainWarpProgressive: FractalType
    FractalType_DomainWarpIndependent: FractalType

class CellularDistanceFunction(Enum):
    CellularDistanceFunction_Euclidean: CellularDistanceFunction
    CellularDistanceFunction_EuclideanSq: CellularDistanceFunction
    CellularDistanceFunction_Manhattan: CellularDistanceFunction
    CellularDistanceFunction_Hybrid: CellularDistanceFunction

class CellularReturnType(Enum):
    CellularReturnType_CellValue: CellularReturnType
    CellularReturnType_Distance: CellularReturnType
    CellularReturnType_Distance2: CellularReturnType
    CellularReturnType_Distance2Add: CellularReturnType
    CellularReturnType_Distance2Sub: CellularReturnType
    CellularReturnType_Distance2Mul: CellularReturnType
    CellularReturnType_Distance2Div: CellularReturnType

class DomainWarpType(Enum):
    DomainWarpType_OpenSimplex2: DomainWarpType
    DomainWarpType_OpenSimplex2Reduced: DomainWarpType
    DomainWarpType_BasicGrid: DomainWarpType

class FastNoiseLite:
    def __init__(self, seed: int = 1337) -> None: ...
    seed: int
    frequency: float
    noise_type: NoiseType
    rotation_type_3d: RotationType3D
    fractal_type: FractalType
    fractal_octaves: int
    fractal_lacunarity: float
    fractal_gain: float
    fractal_weighted_strength: float
    fractal_ping_pong_strength: float
    cellular_distance_function: CellularDistanceFunction
    cellular_return_type: CellularReturnType
    cellular_jitter: float
    domain_warp_type: DomainWarpType
    domain_warp_amp: float
    def get_noise(self, x: float, y: float, z: float | None = None) -> float: ...
    def gen_from_coords(
        self, coords: NDArray[np.float32]
    ) -> NDArray[np.float32]: ...
