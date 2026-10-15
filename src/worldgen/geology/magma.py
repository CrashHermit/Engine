"""Magma intensity and flow generation."""

import numpy as np

from src.worldgen.field.noise import fbm
from src.worldgen.field.vector import gradient
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.config import MagmaConfig
from src.worldgen.utilities.normalize import interpolate_values, scale_vector_magnitudes


def generate_magma(
    mesh: Mesh, config: MagmaConfig, *, noise_seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Return normalized magma intensity and its tangent velocity field."""
    raw_intensity = fbm(
        mesh.vertices,
        seed=noise_seed,
        octaves=config.octaves,
        base_frequency=config.base_frequency,
        lacunarity=config.lacunarity,
        persistence=config.persistence,
    )
    intensity = interpolate_values(raw_intensity, (0.0, 1.0))
    velocity = scale_vector_magnitudes(
        gradient(mesh, intensity, descending=config.descending)
    )
    intensity.setflags(write=False)
    velocity.setflags(write=False)
    return intensity, velocity
