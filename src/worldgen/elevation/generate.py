"""Build elevation definitions once; gameplay meshes sample them independently."""

import numpy as np

from src.worldgen.elevation.bounds import elevation_bounds
from src.worldgen.elevation.config import ElevationConfig
from src.worldgen.elevation.deformation import TectonicField
from src.worldgen.elevation.field import ElevationField
from src.worldgen.elevation.volcanism import VolcanicField
from src.worldgen.geology.config import CrustDensityConfig
from src.worldgen.geology.model import GeologyResult
from src.worldgen.geometry.boundary import BoundaryNetwork, SphericalRegions
from src.worldgen.geometry.mesh import Mesh


def generate_elevation_field(
    mesh: Mesh,
    config: ElevationConfig,
    radius_m: float,
    *,
    geology: GeologyResult,
    density_config: CrustDensityConfig,
    density_noise_seed: int,
    noise_seeds: tuple[int, int, int],
    arc_noise_seed: int,
) -> ElevationField:
    """Retain established geography, spatial indexes, noise seeds, and profiles."""
    regions = SphericalRegions(mesh)
    crust_boundary = BoundaryNetwork(mesh, geology.crust.continental_mask)
    plate_boundary = BoundaryNetwork(
        mesh, geology.plate_ids, geology.boundary_edge_indices
    )
    tectonics = TectonicField(
        mesh,
        geology,
        config.deformation,
        boundary=plate_boundary,
        arc_noise_seed=arc_noise_seed,
    )
    volcanoes = VolcanicField(
        mesh, geology.plate_ids, geology.hotspots, geology.volcanism.sites, regions
    )
    max_shield_height = max(
        float(np.max(geology.hotspots.heights_percent, initial=0.0)),
        float(np.max(geology.volcanism.sites.heights_percent, initial=0.0)),
    )
    total_range, base_range = elevation_bounds(
        config,
        1.0,
        density_variation=density_config.variation_strength,
        max_motion=tectonics.max_motion,
        max_shield_height_percent=max_shield_height,
    )
    return ElevationField(
        config=config,
        radius_m=radius_m,
        regions=regions,
        continental_mask=geology.crust.continental_mask,
        crust_boundary=crust_boundary,
        plate_boundary=plate_boundary,
        density_config=density_config,
        density_noise_seed=density_noise_seed,
        width_noise_seeds=noise_seeds,
        tectonics=tectonics,
        volcanoes=volcanoes,
        elevation_range_fraction=total_range,
        base_elevation_range_fraction=base_range,
    )
