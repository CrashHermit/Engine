import numpy as np

from src.core.geometry.mesh import generate_icosphere, Mesh
from src.worldgen.render.render import Render
from src.worldgen.generator.geology import Geology


def main() -> None:
    vertices, faces = generate_icosphere(nu=30)

    mesh = Mesh(vertices, faces)

    geology = Geology(mesh=mesh)

    intensity = geology.generate_magma_intensity(
        octaves=8, base_frequency=6.0, lacunarity=3.0, persistence=0.7
    )

    plate_regions = geology.generate_plate_regions(
        node_values=intensity,
        num_points=15,
        min_distance=0.2,
        max_retries=10,
        strength=1.0,
    )

    magma_velocity = geology.generate_magma_velocity(node_values=intensity, descending=True)

    plate_velocity = geology.generate_plate_velocity(magma_velocity=magma_velocity, plate_regions=plate_regions)

    renderer = Render(mesh=mesh, plates=plate_regions, plate_velocity=plate_velocity)

    renderer.show_plates(arrow_scale=0.08)


if __name__ == "__main__":
    main()
