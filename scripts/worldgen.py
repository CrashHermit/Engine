from src.worldgen.generator.magma_flow import MagmaFlow
from src.worldgen.geometry.mesh import Mesh
from src.script.render import Render


class Worldgen:
    def __init__(self) -> None:
        pass

    def display_magma(self):
        pass


if __name__ == "__main__":
    mesh = Mesh(nu=30, radius=1.0)

    flow_model = MagmaFlow(mesh=mesh)
    flow_vectors = flow_model.generate_magma_flow(
        octaves=4, base_frequency=1.0, lacunarity=2.0, persistence=0.5
    )

    renderer = Render(
        vertex_array=mesh.vertices,
        dual_vertices=mesh.dual_vertices,
        dual_faces=mesh.dual_faces,
    )
    renderer.display()
