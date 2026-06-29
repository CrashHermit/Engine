import numpy as np
import opensimplex as osn


class Generator:
    def __init__(self, tiles: dict):
        self.tiles: dict = tiles

    def generate_3d_fbm(
        self,
        xs: np.ndarray,
        ys: np.ndarray,
        zs: np.ndarray,
        octaves: int,
        base_frequency: float,
        lacunarity: float,
        persistence: float,
    ) -> np.ndarray:

        elevations = np.zeros(len(xs), dtype=np.double)

        amplitude = 1.0
        frequency = base_frequency
        total_amplitude = 0.0

        for octave in range(octaves):
            shift = octave * 1123.456

            noise_layer = osn.noise3array(
                (xs * frequency) + shift,
                (ys * frequency) + shift,
                (zs * frequency) + shift,
            )

            elevations += noise_layer * amplitude
            total_amplitude += amplitude

            amplitude *= persistence
            frequency *= lacunarity

        return elevations / total_amplitude

    def calculate_gradient_field(
        self, scalar_attribute: str, vector_name: str, flow_downhill: bool = False
    ):
        """
        Calculates a general vector field across the entire planet based on ANY scalar attribute.

        scalar_attribute: The name of the variable to read (e.g., "elevation", "pressure")
        vector_name: The name to save the resulting vector under (e.g., "magma_flow", "wind")
        flow_downhill: If True, vectors point from High to Low (Magma). If False, Low to High.
        """
        print(
            f"Calculating general vector field '{vector_name}' from '{scalar_attribute}'..."
        )

        for tile in self.tiles.values():
            vec_x, vec_y, vec_z = 0.0, 0.0, 0.0

            base_val = getattr(tile, scalar_attribute)

            for neighbor_id in tile.neighbors:
                neighbor = self.tiles[neighbor_id]
                neighbor_val = getattr(neighbor, scalar_attribute)

                delta = neighbor_val - base_val
                if flow_downhill:
                    delta = -delta

                dir_x = neighbor.x - tile.x
                dir_y = neighbor.y - tile.y
                dir_z = neighbor.z - tile.z

                vec_x += dir_x * delta
                vec_y += dir_y * delta
                vec_z += dir_z * delta

            dot_product = (vec_x * tile.x) + (vec_y * tile.y) + (vec_z * tile.z)

            final_x = vec_x - (dot_product * tile.x)
            final_y = vec_y - (dot_product * tile.y)
            final_z = vec_z - (dot_product * tile.z)

            tile.vectors[vector_name] = (final_x, final_y, final_z)

        print(f"Vector field '{vector_name}' generated successfully.")
