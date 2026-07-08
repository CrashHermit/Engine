import numpy as np

from src.core.field.vector.operator import gradient, surface_curl
from src.core.field.scalar.cost import noise_average, noise_multiplicative
from src.core.field.scalar.noise import fbm
from src.core.field.scalar.voronoi import voronoi_msd
from src.core.utilities.groupby import grouped_mean
from src.core.utilities.normalize import (
    interpolate_values,
    scale_vector_magnitudes,
)
from src.core.utilities.sampling import poisson_disk_sample
from src.core.geometry.mesh import Mesh


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

    def generate_plate_regions(
        self,
        node_values: np.ndarray,
        num_points: int,
        min_distance: float,
        max_retries: int,
        strength: float,
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

        edge_weights: dict[tuple[int, int], float] = noise_multiplicative(
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

        gradient_vectors: np.ndarray = gradient(
            positions=positions,
            adjacency=adjacency,
            node_values=node_values,
            descending=descending,
        )

        curl_vectors: np.ndarray = surface_curl(
            positions=positions,
            adjacency=adjacency,
            node_values=node_values
        )

        vectors = gradient_vectors + curl_vectors

        normalized_vectors: np.ndarray = scale_vector_magnitudes(vectors=vectors)

        return normalized_vectors

    def generate_plate_velocity(self, magma_velocity: np.ndarray, plate_regions: dict[int, int]) -> np.ndarray:
        positions: np.ndarray = self.mesh.vertices
        plate_ids: np.ndarray = np.array([plate_regions[i] for i in range(len(magma_velocity))], dtype=int)

        # 1. Calculate pure angular momentum from the (now swirling!) magma
        angular_momenta: np.ndarray = np.cross(positions, magma_velocity)
        
        # 2. Average it to find the plate's true physical Euler Pole
        plate_omega: np.ndarray = grouped_mean(values=angular_momenta, group_ids=plate_ids)

        # 3. Apply it to the cells
        cell_omega: np.ndarray = plate_omega[plate_ids]
        cell_velocities: np.ndarray = np.cross(cell_omega, positions)

        # 4. Global scaling (0.0 to 1.0)
        speeds: np.ndarray = np.linalg.norm(cell_velocities, axis=1, keepdims=True)
        max_speed = np.max(speeds)
        
        if max_speed > 0:
            return cell_velocities / max_speed
        return cell_velocities
