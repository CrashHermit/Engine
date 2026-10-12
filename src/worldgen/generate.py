"""Top-level orchestration for the current procedural world stages."""

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geology import generate_geology
from src.worldgen.model import GeneratedWorld


def _signed_seed(sequence: np.random.SeedSequence) -> int:
    value = int(sequence.generate_state(1, dtype=np.uint64)[0])
    return value if value < 2**63 else value - 2**64


def generate_world(config: WorldgenConfig) -> GeneratedWorld:
    """Generate a seeded spherical mesh and its current geology fields."""
    noise_sequence, sampling_sequence = np.random.SeedSequence(config.seed).spawn(2)
    vertices, faces = generate_icosphere(config.subdivision_frequency)
    mesh = Mesh(vertices, faces)
    geology = generate_geology(
        mesh,
        config.geology,
        noise_seed=_signed_seed(noise_sequence),
        seed_rng=np.random.default_rng(sampling_sequence),
    )
    return GeneratedWorld(mesh=mesh, geology=geology)
