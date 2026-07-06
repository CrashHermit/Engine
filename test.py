from src.core.geometry.mesh import generate_icosphere, Mesh
from src.worldgen.render.render import Render
from src.worldgen.generator.geology import Geology


def main() -> None:
    vertices, faces = generate_icosphere(nu=8)

    mesh = Mesh(vertices, faces)

    geology = Geology(mesh=mesh)

    intensity = geology.generate_magma_intensity(
        octaves=4, base_frequency=2.0, lacunarity=2.0, persistence=0.5
    )

    plates = geology.generate_plates(
        node_values=intensity,
        num_points=12,
        min_distance=0.3,
        max_retries=10,
        strength=1.0,
    )

    velocity = geology.generate_magma_velocity(node_values=intensity, descending=True)

    renderer = Render(mesh=mesh, plates=plates, velocity=velocity)

    renderer.show_plates(arrow_scale=0.08)

if __name__ == "__main__":
    main()
