"""Top-level orchestration for world generation."""

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geology import generate_geology
from src.worldgen.terrain.generate import generate_terrain
from src.worldgen.model import GeneratedWorld


def _signed_seed(sequence: np.random.SeedSequence) -> int:
    value = int(sequence.generate_state(1, dtype=np.uint64)[0])
    return value if value < 2**63 else value - 2**64


def generate_world(config: WorldgenConfig) -> GeneratedWorld:
    """Generate a seeded spherical mesh and its geology and terrain fields."""
    magma_noise, plate_sampling, crust_noise, crust_sampling, plate_growth = (
        np.random.SeedSequence(config.seed).spawn(5)
    )
    vertices, faces = generate_icosphere(config.subdivision_frequency)
    mesh = Mesh(vertices, faces)
    geology = generate_geology(
        mesh,
        config.geology,
        magma_noise_seed=_signed_seed(magma_noise),
        plate_seed_rng=np.random.default_rng(plate_sampling),
        plate_noise_seed=_signed_seed(plate_growth),
        crust_noise_seed=_signed_seed(crust_noise),
        crust_rng=np.random.default_rng(crust_sampling),
    )
    terrain = generate_terrain(
        mesh, geology.crust.continental_mask, config.terrain, config.planet.radius_m
    )
    return GeneratedWorld(mesh=mesh, geology=geology, terrain=terrain)
