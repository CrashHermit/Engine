import numpy as np

from worldgen.field.gradient import Gradient
from worldgen.geometry.mesh import Mesh
from worldgen.scalar.noise import generate_3d_fbm
from worldgen.transform.normalize import scale_vector_magnitudes


class MagmaFlow:
    def __init__(
        self,
        mesh: Mesh,
        octaves: int,
        base_frequency: float,
        lacunarity: float,
        persistence: float,
    ) -> None:
        self.mesh = mesh
        self.octaves = octaves
        self.base_frequency = base_frequency
        self.lacunarity = lacunarity
        self.persistence = persistence

        self.magma_scalar_values = self._generate_magma_scalar_values()
        self.magma_vector_fields = self._generate_magma_vector_field()

    def generate(self) -> np.ndarray:
        if self._flow is None:
            self._flow = self._compute_flow()
        return self._flow

    def _generate_magma_scalar_values(self) -> np.ndarray:

        positions = self.mesh.vertices
        neighbors = self.mesh.neighbors
        base_frequency

        fbm: np.ndarray = generate_3d_fbm(
            positions=self.mesh.positions,
            octaves=octaves,
            base_frequency=base_frequency,
            lacunarity=lacunarity,
            persistence=persistence,
        )

        return flow

    def _generate_magma_vector_field(positions: np.ndarray, neighbors: np.ndarray) -> np.ndarray:
        gradient: Gradient = Gradient(positions=positions, neighbors=neighbors)
        flow: np.ndarray = gradient.batch(values=fbm, descending=True)
        flow: np.ndarray = scale_vector_magnitudes(vectors=flow)
        return flow
