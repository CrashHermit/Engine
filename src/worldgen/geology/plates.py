"""Plate partition and coherent motion generation."""

import numpy as np

from src.worldgen.field.cost import field_traversal_cost
from src.worldgen.field.partition import (
    priority_flood_regions,
    region_boundary_edges,
    weighted_regions,
)
from src.worldgen.field.priority import noise_biased_priorities
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.config import PlateConfig
from src.worldgen.geology.model import PlateResult
from src.worldgen.utilities.groupby import grouped_mean
from src.worldgen.utilities.normalize import scale_vector_magnitudes
from src.worldgen.utilities.sampling import poisson_disk_sample


def generate_plate_regions(
    mesh: Mesh,
    config: PlateConfig,
    magma_intensity: np.ndarray,
    *,
    seed_rng: np.random.Generator,
    noise_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return plate seed vertex indices and each vertex's plate owner."""
    seed_indices = poisson_disk_sample(
        mesh.vertices, config.plate_count, config.min_seed_distance, rng=seed_rng
    )
    if config.growth_method == "priority-flood":
        priorities = noise_biased_priorities(
            mesh.vertices, seed_indices, config.flood, noise_seed=noise_seed
        )
        plate_ids = priority_flood_regions(mesh, seed_indices, priorities)
    else:
        edge_costs = field_traversal_cost(
            mesh, magma_intensity, config.irregularity_strength
        )
        plate_ids = weighted_regions(mesh, seed_indices, edge_costs)
    seed_indices.setflags(write=False)
    plate_ids.setflags(write=False)
    return seed_indices, plate_ids


def calculate_plate_rotation(
    mesh: Mesh, magma_velocity: np.ndarray, plate_ids: np.ndarray
) -> np.ndarray:
    """Calculate mean angular momentum for each plate."""
    plate_rotation = grouped_mean(np.cross(mesh.vertices, magma_velocity), plate_ids)
    plate_rotation.setflags(write=False)
    return plate_rotation


def calculate_plate_velocity(
    mesh: Mesh, plate_rotation: np.ndarray, plate_ids: np.ndarray
) -> np.ndarray:
    """Calculate tangent velocity from each vertex's plate rotation."""
    plate_velocity = scale_vector_magnitudes(
        np.cross(plate_rotation[plate_ids], mesh.vertices)
    )
    plate_velocity.setflags(write=False)
    return plate_velocity


def generate_plates(
    mesh: Mesh,
    config: PlateConfig,
    magma_intensity: np.ndarray,
    magma_velocity: np.ndarray,
    *,
    seed_rng: np.random.Generator,
    noise_seed: int,
) -> PlateResult:
    """Generate plate regions, motion, and boundary edge indices."""
    seed_indices, plate_ids = generate_plate_regions(
        mesh, config, magma_intensity, seed_rng=seed_rng, noise_seed=noise_seed
    )
    plate_rotation = calculate_plate_rotation(mesh, magma_velocity, plate_ids)
    plate_velocity = calculate_plate_velocity(mesh, plate_rotation, plate_ids)
    boundary_edge_indices = region_boundary_edges(mesh, plate_ids)
    return PlateResult(
        seed_indices=seed_indices,
        plate_ids=plate_ids,
        plate_rotation=plate_rotation,
        plate_velocity=plate_velocity,
        boundary_edge_indices=boundary_edge_indices,
    )
