import numpy as np

from core.field.vector.gradient import gradient
from core.geometry.mesh import Mesh
from core.field.scalar.noise import generate_3d_fbm
from core.utilities.normalize import scale_vector_magnitudes
from src.core.utilities.sampling import poisson_disk_sample
from src.worldgen.scalar.voronoi import voronoi_msd


class Geology:
    def __init__(
        self,
        mesh: Mesh,
        octaves: int,
        base_frequency: float,
        lacunarity: float,
        persistence: float,
        descending: bool,
    ) -> None:
        self.mesh = mesh
        self.octaves = octaves
        self.base_frequency = base_frequency
        self.lacunarity = lacunarity
        self.persistence = persistence
        self.descending = descending

        self.magma_scalar_values = self._generate_magma_scalar_values()
        self.plates = self._generate_plates()
        self.magma_vector_fields = self._generate_magma_vector_field()

    def _generate_magma_intensity(self) -> np.ndarray:
        fbm: np.ndarray = generate_3d_fbm(
            positions=self.mesh.verties,
            octaves=self.octaves,
            base_frequency=self.base_frequency,
            lacunarity=self.lacunarity,
            persistence=self.persistence,
        )

        return flow

    def _generate_plates(self) -> list[int]:
        plate_seeds: list[int] = poisson_disk_sample(
            positions=self.mesh.vertices,
            num_points=self.num_plates,
            min_distance=self.min_distance,
            max_retries=self.max_retries,
        )

        plate_regions = voronoi_msd()
        

    def _generate_magma_flow(self) -> np.ndarray:
        vector_field: np.ndarray = gradient(
            positions=self.mesh.vertices,
            neighbors=self.mesh.neighbors,
            values=self.magma_scalar_values,
            descending=True,
        )
        return vecltor_field
