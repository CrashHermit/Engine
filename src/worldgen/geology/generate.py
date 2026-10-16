"""Orchestration of magma, plates, boundaries, and crust generation."""

import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.boundary import boundary_interactions
from src.worldgen.geology.boundary_sections import generate_boundary_sections
from src.worldgen.geology.config import GeologyConfig
from src.worldgen.geology.crust import generate_crust
from src.worldgen.geology.magma import generate_magma
from src.worldgen.geology.model import GeologyResult
from src.worldgen.geology.plates import generate_plates


def generate_geology(
    mesh: Mesh,
    config: GeologyConfig,
    *,
    magma_noise_seed: int,
    plate_seed_rng: np.random.Generator,
    plate_motion_rng: np.random.Generator,
    plate_noise_seed: int,
    crust_noise_seed: int,
    crust_rng: np.random.Generator,
    density_noise_seed: int,
) -> GeologyResult:
    """Generate geology and its boundary metadata using independent streams."""
    magma_intensity, magma_velocity = generate_magma(
        mesh, config.magma, noise_seed=magma_noise_seed
    )
    plates = generate_plates(
        mesh,
        config.plates,
        magma_intensity,
        seed_rng=plate_seed_rng,
        plate_motion_rng=plate_motion_rng,
        noise_seed=plate_noise_seed,
    )
    convergence, divergence, shear = boundary_interactions(
        mesh,
        plates.plate_ids,
        plates.plate_rotation,
        plates.boundary_edge_indices,
    )
    crust = generate_crust(
        mesh,
        config.crust,
        noise_seed=crust_noise_seed,
        density_noise_seed=density_noise_seed,
        rng=crust_rng,
    )
    sections = generate_boundary_sections(
        mesh,
        plates.plate_ids,
        crust,
        plates.boundary_edge_indices,
    )
    for array in (convergence, divergence, shear):
        array.setflags(write=False)
    return GeologyResult(
        magma_intensity=magma_intensity,
        seed_indices=plates.seed_indices,
        plate_ids=plates.plate_ids,
        magma_velocity=magma_velocity,
        plate_rotation=plates.plate_rotation,
        plate_velocity=plates.plate_velocity,
        boundary_edge_indices=plates.boundary_edge_indices,
        boundary_convergence=convergence,
        boundary_divergence=divergence,
        boundary_shear=shear,
        boundary_sections=sections,
        crust=crust,
    )
