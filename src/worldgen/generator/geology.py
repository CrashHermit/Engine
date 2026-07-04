from dataclasses import dataclass

import numpy as np

from core.field.vector.gradient import gradient
from core.geometry.mesh import Mesh
from src.core.field.scalar.noise import fbm

from src.core.utilities.sampling import poisson_disk_sample
from src.worldgen.scalar.voronoi import voronoi_msd

@dataclass(slots=True)
class GeologyResult:
    magma_intensity: np.ndarray
    plate_regions: dict[int, int]
    magma_velocity: np.ndarray

class Geology:
    def __init__(self, mesh: Mesh) -> None:
        self.mesh = mesh

    def generate_magma_intensity(
        self,
        positions: np.ndarray,
        octaves: int = 4,
        base_frequency: float = 1.0,
        lacunarity: float = 2.0,
        persistence: float = 0.5,
    ) -> np.ndarray:
        intensity: np.ndarray = fbm(
            positions=positions,
            octaves=octaves,
            base_frequency=base_frequency,
            lacunarity=lacunarity,
            persistence=persistence,
        )

        return intensity

    def generate_plates(
        self,
        positions: np.ndarray,
        adjacency: list[list[int]],
        num_points: int,
        min_distance: float,
        max_retries: int,
    ) -> dict[int, int]:
        seed_indices: list[int] = poisson_disk_sample(
            positions=positions,
            num_points=num_points,
            min_distance=min_distance,
            max_retries=max_retries,
        )

        seeds: dict[int, int] = {
            idx: pid for pid, idx in enumerate(seed_indices)
        }

        def _cost(a: int, b: int) -> float:
            return float(np.linalg.norm(positions[a] - positions[b]))

        plate_regions: dict[int, int] = voronoi_msd(
            adjacency=adjacency,
            seeds=seeds,
            cost_function=_cost,
        )

        return plate_regions

    def generate_magma_flow(
        self,
        positions: np.ndarray,
        neighbors: list[list[int]],
        scalar_values: np.ndarray,
        descending: bool = True,
    ) -> np.ndarray:
        vector_field: np.ndarray = gradient(
            positions=positions,
            neighbors=neighbors,
            values=scalar_values,
            descending=descending,
        )
        return vector_field
