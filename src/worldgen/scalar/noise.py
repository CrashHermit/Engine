import numpy as np
import opensimplex as osn


def fbm(
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

        noise_layer = np.zeros_like(elevations)
        for i in range(len(xs)):
            noise_layer[i] = osn.noise3(
                (xs[i] * frequency) + shift,
                (ys[i] * frequency) + shift,
                (zs[i] * frequency) + shift,
            )

        elevations += noise_layer * amplitude
        total_amplitude += amplitude

        amplitude *= persistence
        frequency *= lacunarity

    return elevations / total_amplitude
