import numpy as np

from worldgen.field.gradient import Gradient
from worldgen.geometry.mesh import Mesh
from worldgen.scalar.noise import generate_3d_fbm
from worldgen.transform.normalize import scale_vector_magnitudes


class MagmaFlow:
    def __init__(self, mesh: Mesh) -> None:
        self.mesh = mesh

    def generate_magma_flow(
        self, octaves: int, base_frequency: float, lacunarity: float, persistence: float
    ) -> np.ndarray:

        coordinates = self.mesh.vertices
        neighbors = self.mesh.neighbors

        fbm: np.ndarray = generate_3d_fbm(
            coordinates=coordinates,
            octaves=octaves,
            base_frequency=base_frequency,
            lacunarity=lacunarity,
            persistence=persistence,
        )

        gradient: Gradient = Gradient(positions=coordinates, neighbors=neighbors)
        flow: np.ndarray = gradient.batch(scalar=fbm, descending=True)
        flow: np.ndarray = scale_vector_magnitudes(vectors=flow)

        return flow
