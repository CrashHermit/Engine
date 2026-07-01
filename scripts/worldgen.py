import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.script.render import Render


class Worldgen:
    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    mesh = Mesh(subdivisions=6)
    mesh_arrays: tuple[np.ndarray, np.ndarray] = mesh.generate_frequency_icosphere(
        nu=10, radius=1.0
    )
    vertex_array: np.ndarray = mesh_arrays[0]
    face_array: np.ndarray = mesh_arrays[1]

    renderer = Render(vertex_array, face_array)
    renderer.display()
