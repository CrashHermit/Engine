"""Independent continental and oceanic region generation."""

import numpy as np

from src.worldgen.field.cost import field_traversal_cost
from src.worldgen.field.noise import fbm
from src.worldgen.field.partition import priority_flood_regions, weighted_regions
from src.worldgen.field.priority import noise_biased_priorities
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.config import CrustConfig
from src.worldgen.geology.model import CrustResult
from src.worldgen.utilities.normalize import interpolate_values
from src.worldgen.utilities.sampling import poisson_disk_sample


def generate_crust(
    mesh: Mesh, config: CrustConfig, *, noise_seed: int, rng: np.random.Generator
) -> CrustResult:
    """Grow jointly spaced seeds and inherit each seed's crust character."""
    count = config.continental_seeds + config.oceanic_seeds
    seeds = poisson_disk_sample(mesh.vertices, count, config.min_seed_distance, rng=rng)
    continental_regions = np.zeros(count, dtype=bool)
    continental_regions[rng.permutation(count)[: config.continental_seeds]] = True
    if config.growth_method == "priority-flood":
        priorities = noise_biased_priorities(
            mesh.vertices, seeds, config.flood, noise_seed=noise_seed
        )
        regions = priority_flood_regions(mesh, seeds, priorities)
        field = interpolate_values(
            priorities[regions, np.arange(len(mesh.vertices))], (0.0, 1.0)
        )
    else:
        field = interpolate_values(
            fbm(
                mesh.vertices,
                seed=noise_seed,
                octaves=config.octaves,
                base_frequency=config.base_frequency,
                lacunarity=config.lacunarity,
                persistence=config.persistence,
            ),
            (0.0, 1.0),
        )
        regions = weighted_regions(
            mesh, seeds, field_traversal_cost(mesh, field, config.irregularity_strength)
        )
    mask = continental_regions[regions]
    for array in (regions, seeds, continental_regions, mask, field):
        array.setflags(write=False)
    return CrustResult(
        region_ids=regions,
        seed_indices=seeds,
        continental_regions=continental_regions,
        continental_mask=mask,
        shaping_field=field,
    )
