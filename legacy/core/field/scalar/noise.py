"""OpenSimplex noise — a scalar field generator.

Provides Fractal Brownian Motion (fBm) over a point cloud using the
``opensimplex`` library for the underlying 3D noise primitive.
"""

import numpy as np
import opensimplex as osn


def fbm(
    positions: np.ndarray,
    *,
    octaves: int = 4,
    base_frequency: float = 1.0,
    lacunarity: float = 2.0,
    persistence: float = 0.5,
) -> np.ndarray:
    """Fractal Brownian Motion (fBm) OpenSimplex noise over a point cloud.

    Accumulates ``octaves`` of noise with exponentially increasing frequency
    and decreasing amplitude.  The result is a scalar field over the input
    mesh, suitable as input to climate, geology, or other worldgen systems.

    Seed the output by calling ``opensimplex.seed()`` before generation.

    Args:
        positions: Vertex positions, shape ``(n, 3)``.
        octaves: Number of frequency bands to sum.
        base_frequency: Frequency at the first octave.
        lacunarity: Frequency multiplier per octave (``> 1``).
        persistence: Amplitude multiplier per octave (``< 1``).

    Returns:
        Raw noise values, shape ``(n,)``.
    """
    px: np.ndarray = positions[:, 0]
    py: np.ndarray = positions[:, 1]
    pz: np.ndarray = positions[:, 2]

    values: np.ndarray = np.zeros(len(positions), dtype=np.double)
    amplitude: float = 1.0
    frequency: float = base_frequency
    _noise3: np.vectorize = np.vectorize(osn.noise3)

    for octave in range(octaves):
        shift: float = octave * 1123.456

        layer: np.ndarray = _noise3(
            px * frequency + shift,
            py * frequency + shift,
            pz * frequency + shift,
        )
        values += layer * amplitude

        amplitude *= persistence
        frequency *= lacunarity

    return values
