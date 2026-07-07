import numpy as np

from src.core.geometry.mesh import generate_icosphere, Mesh
from src.core.utilities.groupby import grouped_mean
from src.core.utilities.normalize import scale_vector_magnitudes
from src.worldgen.render.render import Render
from src.worldgen.generator.geology import Geology


def main() -> None:
    vertices, faces = generate_icosphere(nu=14)

    mesh = Mesh(vertices, faces)

    geology = Geology(mesh=mesh)

    intensity = geology.generate_magma_intensity(
        octaves=4, base_frequency=2.0, lacunarity=2.0, persistence=0.5
    )

    plate_regions = geology.generate_plate_regions(
        node_values=intensity,
        num_points=12,
        min_distance=0.3,
        max_retries=10,
        strength=1.0,
    )

    magma_velocity = geology.generate_magma_velocity(node_values=intensity, descending=True)

    plate_velocity = geology.generate_plate_velocity(magma_velocity=magma_velocity, plate_regions=plate_regions)

    renderer = Render(mesh=mesh, plates=plate_regions, plate_velocity=plate_velocity)

    renderer.show_plates(arrow_scale=0.08)


if __name__ == "__main__":
    main()
