from dataclasses import dataclass

import numpy as np

from src.core.field.vector.gradient import gradient
from src.core.field.scalar.cost import noise_average
from src.core.field.scalar.noise import fbm
from src.core.field.scalar.voronoi import voronoi_msd
from src.core.utilities.normalize import interpolate_values, scale_vector_magnitudes
from src.core.utilities.sampling import poisson_disk_sample
from src.core.geometry.mesh import Mesh


@dataclass
class MagmaIntensityConfig:
    octaves: int
    base_frequency: float
    lacunarity: float
    persistence: float


@dataclass
class PlatesConfig:
    num_points: int
    min_distance: float
    max_retries: int
    strength: float


@dataclass
class MagmaVelocityConfig:
    descending: bool = True


class Geology:
    def __init__(self, mesh: Mesh) -> None:
        self.mesh: Mesh = mesh

    def generate_magma_intensity(
        self,
        octaves: int,
        base_frequency: float,
        lacunarity: float,
        persistence: float,
    ) -> np.ndarray:

        positions: np.ndarray = self.mesh.vertices

        raw_noise: np.ndarray = fbm(
            positions=positions,
            octaves=octaves,
            base_frequency=base_frequency,
            lacunarity=lacunarity,
            persistence=persistence,
        )

        domain: tuple[float, float] = (0.0, 1.0)

        intensity: np.ndarray = interpolate_values(
            values=raw_noise,
            domain=domain,
        )

        return intensity

    def generate_plates(
        self,
        node_values: np.ndarray,
        num_points: int,
        min_distance: float,
        max_retries: int,
        strength: float
    ) -> dict[int, int]:

        positions: np.ndarray = self.mesh.vertices
        adjacency: list[list[int]] = self.mesh.neighbors

        seed_indices: list[int] = poisson_disk_sample(
            positions=positions,
            num_points=num_points,
            min_distance=min_distance,
            max_retries=max_retries,
        )

        seeds: dict[int, int] = {idx: pid for pid, idx in enumerate(seed_indices)}

        edge_weights: dict[tuple[int, int], float] = noise_average(
            adjacency=adjacency, node_values=node_values, strength=strength
        )

        plate_regions: dict[int, int] = voronoi_msd(
            adjacency=adjacency,
            seeds=seeds,
            edge_weights=edge_weights,
        )

        return plate_regions

    def generate_magma_velocity(
        self,
        node_values: np.ndarray,
        descending: bool,
    ) -> np.ndarray:

        positions = self.mesh.vertices
        adjacency = self.mesh.neighbors

        vectors: np.ndarray = gradient(
            positions=positions,
            adjacency=adjacency,
            node_values=node_values,
            descending=descending,
        )

        normalized_vectors: np.ndarray = scale_vector_magnitudes(vectors=vectors)

        return normalized_vectors
