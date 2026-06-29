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


