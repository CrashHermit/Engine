"""Top-level orchestration for world generation."""

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation import generate_elevation
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geology import generate_geology
from src.worldgen.model import GeneratedWorld


def _signed_seed(sequence: np.random.SeedSequence) -> int:
    value = int(sequence.generate_state(1, dtype=np.uint64)[0])
    return value if value < 2**63 else value - 2**64


def generate_world(config: WorldgenConfig) -> GeneratedWorld:
    """Generate a seeded spherical mesh, geology, and elevation fields."""
    streams = np.random.SeedSequence(config.seed).spawn(12)
    potential_noise, plate_sampling, crust_noise, crust_sampling, plate_growth = (
        streams[:5]
    )
    vertices, faces = generate_icosphere(config.subdivision_frequency)
    mesh = Mesh(vertices, faces)
    geology = generate_geology(
        mesh,
        config.geology,
        potential_noise_seed=_signed_seed(potential_noise),
        plate_seed_rng=np.random.default_rng(plate_sampling),
        plate_motion_rng=np.random.default_rng(streams[9]),
        plate_noise_seed=_signed_seed(plate_growth),
        crust_noise_seed=_signed_seed(crust_noise),
        crust_rng=np.random.default_rng(crust_sampling),
        density_noise_seed=_signed_seed(streams[8]),
        hotspot_rng=np.random.default_rng(streams[11]),
    )
    elevation = generate_elevation(
        mesh,
        config.elevation,
        config.planet.radius_m,
        crust=geology.crust,
        plate_ids=geology.plate_ids,
        boundary_edge_indices=geology.boundary_edge_indices,
        boundary_sections=geology.boundary_sections,
        boundary_convergence=geology.boundary_convergence,
        boundary_divergence=geology.boundary_divergence,
        boundary_shear=geology.boundary_shear,
        noise_seeds=tuple(_signed_seed(stream) for stream in streams[5:8]),
        hotspots=geology.hotspots,
        arc_noise_seed=_signed_seed(streams[10]),
    )
    return GeneratedWorld(
        mesh=mesh,
        geology=geology,
        elevation=elevation,
        radius_m=config.planet.radius_m,
    )
