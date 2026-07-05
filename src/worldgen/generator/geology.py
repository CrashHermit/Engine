from dataclasses import dataclass

import numpy as np

from core.field.vector.gradient import gradient
from core.geometry.mesh import Mesh
from src.core.field.scalar.cost import noise_average
from src.core.field.scalar.noise import fbm
from src.core.field.scalar.voronoi import voronoi_msd

from src.core.utilities.normalize import interpolate_values, scale_vector_magnitudes
from src.core.utilities.sampling import poisson_disk_sample


@dataclass
class MagmaIntensityConfig:
    octaves: int
    base_frequency: float
    lacunarity: float
    persistence: float


@dataclass
class PlatesConfig:
    edge_weights: dict[tuple[int, int], float]
    num_points: int
    min_distance: float
    max_retries: int


@dataclass
class MagmaVelocityConfig:
    node_values: np.ndarray
    descending: bool = True


@dataclass
class GeologyReturn:
    pass


class Geology:
    def __init__(self, mesh: Mesh) -> None:
        self.mesh = mesh
        self.raw_noise = None

    def _generate_magma_intensity(
        self,
        octaves: int,
        base_frequency: float,
        lacunarity: float,
        persistence: float,
    ) -> np.ndarray:

        positions: np.ndarray = self.mesh.vertices

        self.raw_noise: np.ndarray = fbm(
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

    def _generate_plates(
        self,
        num_points: int,
        min_distance: float,
        max_retries: int,
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

        node_values: np.ndarray = self.raw_noise

        edge_weights: dict[tuple[int, int], float] = noise_average(
            adjacency=adjacency,
            node_values=
        )

        plate_regions: dict[int, int] = voronoi_msd(
            adjacency=adjacency,
            seeds=seeds,
            edge_weights=edge_weights,
        )

        return plate_regions

    def _generate_magma_velocity(
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

    def generate(
        self,
        magma_intensity_config: MagmaIntensityConfig,
        plates_config: PlatesConfig,
        magma_velocity_config: MagmaVelocityConfig,
    ) -> None:

        octaves: int = magma_intensity_config.octaves
        base_frequency: float = magma_intensity_config.base_frequency
        lacunarity: float = magma_intensity_config.lacunarity
        persistence: float = magma_intensity_config.persistence

        magma_intensity: np.ndarray = self._generate_magma_intensity(
            octaves=octaves,
            base_frequency=base_frequency,
            lacunarity=lacunarity,
            persistence=persistence,
        )

        num_points: int = plates_config.num_points
        min_distance: float = plates_config.min_distance
        max_retries: int = plates_config.max_retries

        plates: dict[int, int] = self._generate_plates(
            edge_weights=edge_weights,
            num_points=num_points,
            min_distance=min_distance,
            max_retries=max_retries,
        )

        node_values: np.ndarray = magma_velocity_config.node_values
        descending: bool = magma_velocity_config.descending

        magma_velocity: np.ndarray = self._generate_magma_vectors(
            node_values=node_values,
            descending=descending,
        )
