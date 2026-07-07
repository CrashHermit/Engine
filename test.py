import numpy as np

from src.core.geometry.mesh import generate_icosphere, Mesh
from src.core.utilities.groupby import grouped_mean
from src.core.utilities.normalize import scale_vector_magnitudes
from src.worldgen.render.render import Render
from src.worldgen.generator.geology import Geology


def main() -> None:
    vertices, faces = generate_icosphere(nu=20)

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

    ids = np.array([plates[i] for i in range(len(velocity))], dtype=int)

    plate_velocities = grouped_mean(velocity, ids)

    tile_velocities = plate_velocities[ids]

    dot = np.sum(tile_velocities * vertices, axis=1, keepdims=True)
    tile_velocities = tile_velocities - dot * vertices


    tile_velocities = scale_vector_magnitudes(tile_velocities)

    renderer = Render(mesh=mesh, plates=plates, plate_velocity=tile_velocities)

    renderer.show_plates(arrow_scale=0.08)


if __name__ == "__main__":
    main()
