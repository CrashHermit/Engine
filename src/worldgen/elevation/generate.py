"""Graph-distance coastal elevation generation."""

import numpy as np

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
from src.worldgen.geology.model import CrustResult
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.geometry.spherical import edge_lengths_percent


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
    noise_seeds: tuple[int, int, int],
    arc_noise_seed: int,
) -> ElevationResult:
    """Generate coastal base elevation and tectonic relief."""
    deformation = config.deformation
    continental_mask = crust.continental_mask
    crust_boundary_edge_indices = region_boundary_edges(mesh, continental_mask)
    lengths = edge_lengths_percent(mesh)
    margin_distance = _signed_margin_distances(
        mesh, continental_mask, crust_boundary_edge_indices, lengths
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
        boundary_divergence=boundary_divergence,
        arc_variation=arc_variation,
    )
    elevation = base_elevation + tectonic
    land_mask = elevation >= 0.0
    for array in (
        margin_distance,
        base_elevation,
        tectonic,
        elevation,
        land_mask,
    ):
        array.setflags(write=False)
    collision = deformation.collision
    subduction = deformation.subduction
    divergence = deformation.divergence
    max_convergence = float(np.max(boundary_convergence, initial=0.0))
    max_divergence = float(np.max(boundary_divergence, initial=0.0))
    collision_bound = collision.height_percent * radius_m * max_convergence / 100.0
    subduction_bound = subduction.height_percent * radius_m * max_convergence / 100.0
    convergence_bound = max(collision_bound, subduction_bound)
    arc_bound = (
        subduction_bound
        * abs(subduction.arc_height_multiplier)
        * (1.0 + abs(subduction.arc_variation_strength))
    )
    divergence_bound = divergence.height_percent * radius_m * max_divergence / 100.0
    lower_relief_bound = (
        convergence_bound
        + arc_bound
        + divergence_bound * divergence.axial_depth_multiplier
    )
    upper_relief_bound = (
        max(
            collision_bound * max(1.0, 1.0 + collision.crest_height_multiplier),
            subduction_bound,
        )
        + arc_bound
        + divergence_bound * max(1.0, divergence.shoulder_height_multiplier)
    )
    density_anomaly_min = float(np.min(crust.density_anomaly))
    density_anomaly_max = float(np.max(crust.density_anomaly))
    base_range = (
        -(
            config.basin_depth_percent
            + config.buoyancy.oceanic_height_percent * density_anomaly_max
        )
        * radius_m
        / 100.0,
        (
            config.interior_height_percent
            - config.buoyancy.continental_height_percent * density_anomaly_min
        )
        * radius_m
        / 100.0,
    )
    return ElevationResult(
        base_elevation=base_elevation,
        tectonic_relief=tectonic,
        elevation=elevation,
        margin_distance=margin_distance,
        land_mask=land_mask,
        crust_boundary_edge_indices=crust_boundary_edge_indices,
        elevation_range_m=(
            base_range[0] - lower_relief_bound,
            base_range[1] + upper_relief_bound,
        ),
        base_elevation_range_m=base_range,
    )
