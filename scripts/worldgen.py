from src.worldgen.geometry.mesh import Mesh
from src.script.render import Render


class Worldgen:
    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    mesh = Mesh(subdivisions=6, nu=10, radius=1.0)

    renderer = Render(
        vertex_array=mesh.vertices,
        dual_vertices=mesh.dual_vertices,
        dual_faces=mesh.dual_faces,
    )
    renderer.display()
