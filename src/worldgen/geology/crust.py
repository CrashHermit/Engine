"""Independent continental and oceanic region generation."""

import numpy as np

from src.worldgen.field.cost import field_traversal_cost
from src.worldgen.field.noise import noise_multiplier, fbm
from src.worldgen.field.partition import priority_flood_regions, weighted_regions
from src.worldgen.field.priority import noise_biased_priorities
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.config import CrustConfig, CrustDensityConfig
from src.worldgen.geology.model import CrustResult
from src.worldgen.utilities.groupby import grouped_mean
from src.worldgen.utilities.normalize import interpolate_values
from src.worldgen.utilities.sampling import poisson_disk_sample


def _crust_density_baseline(
    continental_mask: np.ndarray, config: CrustDensityConfig
) -> np.ndarray:
    """Return the per-cell reference density used by the density field."""
    return np.where(
        continental_mask, config.continental_base, config.oceanic_base
    ).astype(np.float64)


def effective_crust_density(
    positions: np.ndarray,
    continental_mask: np.ndarray,
    config: CrustDensityConfig,
    *,
    noise_seed: int,
) -> np.ndarray:
    """Generate a dimensionless effective-density proxy for each cell."""
    base = _crust_density_baseline(continental_mask, config)
    return base * noise_multiplier(
        positions,
        seed=noise_seed,
        frequency=config.noise_frequency,
        strength=config.variation_strength,
    )


def generate_crust(
    mesh: Mesh,
    config: CrustConfig,
    *,
    noise_seed: int,
    density_noise_seed: int,
    rng: np.random.Generator,
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
                octaves=config.field.octaves,
                base_frequency=config.field.base_frequency,
                lacunarity=config.field.lacunarity,
                persistence=config.field.persistence,
            ),
            (0.0, 1.0),
        )
        regions = weighted_regions(
            mesh, seeds, field_traversal_cost(mesh, field, config.irregularity_strength)
        )
    mask = continental_regions[regions]
    density = effective_crust_density(
        mesh.vertices,
        mask,
        config.density,
        noise_seed=density_noise_seed,
    )
    baseline_density = _crust_density_baseline(mask, config.density)
    density_anomaly = density / baseline_density - 1.0
    region_density = grouped_mean(density, regions)
    for array in (
        regions,
        seeds,
        continental_regions,
        mask,
        field,
        density,
        density_anomaly,
        region_density,
    ):
        array.setflags(write=False)
    return CrustResult(
        region_ids=regions,
        seed_indices=seeds,
        continental_regions=continental_regions,
        continental_mask=mask,
        shaping_field=field,
        effective_density=density,
        density_anomaly=density_anomaly,
        region_effective_density=region_density,
    )
