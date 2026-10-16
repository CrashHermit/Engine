"""Conservative elevation ranges derived from generation settings."""

import numpy as np

from src.worldgen.elevation.config import ElevationConfig
from src.worldgen.elevation.transform import transform_strength
from src.worldgen.geology.model import CrustResult, HotspotResult


def elevation_bounds(
    config: ElevationConfig,
    radius_m: float,
    crust: CrustResult,
    boundary_convergence: np.ndarray,
    boundary_divergence: np.ndarray,
    boundary_shear: np.ndarray,
    hotspots: HotspotResult,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return conservative total and base elevation ranges in metres."""
    deformation = config.deformation
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
    transform = deformation.transform
    max_transform_amplitude = (
        float(
            np.max(
                np.abs(
                    transform_strength(
                        boundary_convergence - boundary_divergence, boundary_shear
                    )
                ),
                initial=0.0,
            )
        )
        if transform.width_percent > 0.0 and transform.height_percent != 0.0
        else 0.0
    )
    transform_bound = (
        abs(transform.height_percent) * radius_m * max_transform_amplitude / 100.0
    )
    lower_relief_bound = (
        convergence_bound
        + arc_bound
        + divergence_bound * divergence.axial_depth_multiplier
        + transform_bound
    )
    upper_relief_bound = (
        max(
            collision_bound * max(1.0, 1.0 + collision.crest_height_multiplier),
            subduction_bound,
        )
        + arc_bound
        + divergence_bound * max(1.0, divergence.shoulder_height_multiplier)
        + transform_bound
    )
    hotspot_bound = (
        float(np.max(hotspots.heights_percent, initial=0.0)) * radius_m / 100.0
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
    return (
        (
            base_range[0] - lower_relief_bound,
            base_range[1] + upper_relief_bound + hotspot_bound,
        ),
        base_range,
    )
