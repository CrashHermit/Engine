"""Top-level orchestration for world generation."""

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation import generate_elevation_field
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geology import generate_geology
from src.worldgen.model import GeneratedWorld
from src.worldgen.field.noise import noise_multiplier


def _signed_seed(sequence: np.random.SeedSequence) -> int:
    value = int(sequence.generate_state(1, dtype=np.uint64)[0])
    return value if value < 2**63 else value - 2**64


def generate_world(config: WorldgenConfig) -> GeneratedWorld:
    """Generate a seeded spherical mesh, geology, and elevation fields."""
    streams = np.random.SeedSequence(config.seed).spawn(13)
    potential_noise, plate_sampling, crust_noise, crust_sampling, plate_growth = (
        streams[:5]
    )
    vertices, faces = generate_icosphere(config.subdivision_frequency)
    mesh = Mesh(vertices, faces)
    deformation = config.elevation.deformation
    arc_variation = noise_multiplier(
        mesh.vertices,
        seed=_signed_seed(streams[10]),
        frequency=deformation.subduction.arc_noise_frequency,
        strength=deformation.subduction.arc_variation_strength,
    )
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
        volcanic_rng=np.random.default_rng(streams[12]),
        subduction_width_percent=deformation.subduction.width_percent,
        arc_offset_fraction=deformation.subduction.arc_offset_fraction,
        arc_width_fraction=deformation.subduction.arc_width_fraction,
        divergence_width_percent=deformation.divergence.width_percent,
        axial_width_fraction=deformation.divergence.axial_width_fraction,
        arc_variation=arc_variation,
    )
    elevation_field = generate_elevation_field(
        mesh,
        config.elevation,
        config.planet.radius_m,
        geology=geology,
        density_config=config.geology.crust.density,
        density_noise_seed=_signed_seed(streams[8]),
        noise_seeds=tuple(_signed_seed(stream) for stream in streams[5:8]),
        arc_noise_seed=_signed_seed(streams[10]),
    )
    elevation = elevation_field.sample(mesh.vertices)
    return GeneratedWorld(
        mesh=mesh,
        geology=geology,
        elevation=elevation,
        radius_m=config.planet.radius_m,
        elevation_field=elevation_field,
    )
