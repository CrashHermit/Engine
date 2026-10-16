"""Graph-distance coastal elevation generation."""

import numpy as np

from src.worldgen.elevation.bounds import elevation_bounds
from src.worldgen.field.partition import region_boundary_edges
from src.worldgen.elevation.coastal import (
    _base_elevation,
    _sample_width,
    _signed_margin_distances,
)
from src.worldgen.elevation.config import ElevationConfig
from src.worldgen.elevation.deformation import tectonic_relief
from src.worldgen.elevation.model import ElevationResult
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geology.model import CrustResult, HotspotResult
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.elevation.volcanism import volcanic_relief


def generate_elevation(
    mesh: Mesh,
    config: ElevationConfig,
    radius_m: float,
    *,
    crust: CrustResult,
    plate_ids: np.ndarray,
    boundary_edge_indices: np.ndarray,
    boundary_sections: BoundarySections,
    boundary_convergence: np.ndarray,
    boundary_divergence: np.ndarray,
    boundary_shear: np.ndarray,
    noise_seeds: tuple[int, int, int],
    arc_noise_seed: int,
    hotspots: HotspotResult,
) -> ElevationResult:
    """Generate coastal base, tectonic, and volcanic relief."""
    deformation = config.deformation
    continental_mask = crust.continental_mask
    crust_boundary_edge_indices = region_boundary_edges(mesh, continental_mask)
    margin_distance = _signed_margin_distances(
        mesh, continental_mask, crust_boundary_edge_indices
    )
    base_elevation = _base_elevation(
        margin_distance,
        config,
        radius_m,
        density_anomaly=crust.density_anomaly,
        inland_width=_sample_width(
            mesh.vertices, config.inland, noise_seed=noise_seeds[0]
        ),
        shelf_width=_sample_width(
            mesh.vertices, config.shelf, noise_seed=noise_seeds[1]
        ),
        slope_width=_sample_width(
            mesh.vertices, config.slope, noise_seed=noise_seeds[2]
        ),
    )

    arc_variation = noise_multiplier(
        mesh.vertices,
        seed=arc_noise_seed,
        frequency=deformation.subduction.arc_noise_frequency,
        strength=deformation.subduction.arc_variation_strength,
    )
    tectonic = tectonic_relief(
        mesh,
        deformation,
        radius_m,
        crust=continental_mask,
        plate_ids=plate_ids,
        boundary_edge_indices=boundary_edge_indices,
        boundary_sections=boundary_sections,
        boundary_convergence=boundary_convergence,
        boundary_shear=boundary_shear,
        boundary_divergence=boundary_divergence,
        arc_variation=arc_variation,
    )
    volcanic = volcanic_relief(mesh, plate_ids, hotspots, radius_m)
    elevation = base_elevation + tectonic + volcanic
    land_mask = elevation >= 0.0
    for array in (
        margin_distance,
        base_elevation,
        tectonic,
        elevation,
        volcanic,
        land_mask,
    ):
        array.setflags(write=False)
    elevation_range, base_range = elevation_bounds(
        config,
        radius_m,
        crust,
        boundary_convergence,
        boundary_divergence,
        boundary_shear,
        hotspots,
    )
    return ElevationResult(
        base_elevation=base_elevation,
        tectonic_relief=tectonic,
        volcanic_relief=volcanic,
        elevation=elevation,
        margin_distance=margin_distance,
        land_mask=land_mask,
        crust_boundary_edge_indices=crust_boundary_edge_indices,
        elevation_range_m=elevation_range,
        base_elevation_range_m=base_range,
    )
