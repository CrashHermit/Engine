"""Generation of procedural plates and their coherent motion."""

import numpy as np

from src.worldgen.field.cost import noise_difference_cost
from src.worldgen.field.noise import fbm
from src.worldgen.field.partition import weighted_regions
from src.worldgen.field.vector import gradient
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.boundary import boundary_interactions
from src.worldgen.geology.config import GeologyConfig
from src.worldgen.geology.model import GeologyResult
from src.worldgen.utilities.groupby import grouped_mean
from src.worldgen.utilities.normalize import interpolate_values, scale_vector_magnitudes
from src.worldgen.utilities.sampling import poisson_disk_sample


def _readonly(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


def generate_geology(
    mesh: Mesh,
    config: GeologyConfig,
    *,
    noise_seed: int,
    seed_rng: np.random.Generator,
) -> GeologyResult:
    """Generate scalar magma variation, plates, flow, and boundaries."""
    raw_intensity = fbm(
        mesh.vertices,
        seed=noise_seed,
        octaves=config.octaves,
        base_frequency=config.base_frequency,
        lacunarity=config.lacunarity,
        persistence=config.persistence,
    )
    magma_intensity = interpolate_values(raw_intensity, (0.0, 1.0))
    seed_indices = poisson_disk_sample(
        mesh.vertices,
        config.plate_count,
        config.min_seed_distance,
        rng=seed_rng,
    )
    edge_costs = noise_difference_cost(mesh, magma_intensity)
    plate_ids = weighted_regions(mesh, seed_indices, edge_costs)
    magma_velocity = scale_vector_magnitudes(
        gradient(mesh, magma_intensity, descending=config.descending)
    )
    angular_momentum = np.cross(mesh.vertices, magma_velocity)
    plate_rotation = grouped_mean(angular_momentum, plate_ids)
    plate_velocity = scale_vector_magnitudes(
        np.cross(plate_rotation[plate_ids], mesh.vertices)
    )
    boundary_edge_indices = np.flatnonzero(
        plate_ids[mesh.edges[:, 0]] != plate_ids[mesh.edges[:, 1]]
    ).astype(np.int64)
    convergence, divergence, shear = boundary_interactions(
        mesh, plate_ids, plate_rotation, boundary_edge_indices
    )
    return GeologyResult(
        magma_intensity=_readonly(magma_intensity),
        seed_indices=_readonly(seed_indices),
        plate_ids=_readonly(plate_ids),
        magma_velocity=_readonly(magma_velocity),
        plate_rotation=_readonly(plate_rotation),
        plate_velocity=_readonly(plate_velocity),
        boundary_edge_indices=_readonly(boundary_edge_indices),
        boundary_convergence=_readonly(convergence),
        boundary_divergence=_readonly(divergence),
        boundary_shear=_readonly(shear),
    )
