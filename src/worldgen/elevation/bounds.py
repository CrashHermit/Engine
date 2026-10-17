"""Conservative elevation ranges from retained source and noise definitions."""

from src.worldgen.elevation.config import ElevationConfig


def elevation_bounds(
    config: ElevationConfig,
    radius_m: float,
    *,
    density_variation: float,
    max_motion: float,
    max_shield_height_percent: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Bound arbitrary samples, not the extrema of a particular sampling mesh."""
    deformation = config.deformation
    collision = deformation.collision
    subduction = deformation.subduction
    divergence = deformation.divergence
    scale = radius_m / 100.0
    collision_bound = abs(collision.height_percent) * scale * max_motion
    subduction_bound = abs(subduction.height_percent) * scale * max_motion
    arc_bound = (
        subduction_bound
        * abs(subduction.arc_height_multiplier)
        * (1.0 + abs(subduction.arc_variation_strength))
    )
    divergence_bound = abs(divergence.height_percent) * scale * max_motion
    # |normal|*shear/(|normal|+shear) <= (|normal|+shear)/4 <= max_motion/2.
    transform_bound = (
        abs(deformation.transform.height_percent) * scale * max_motion / 2.0
    )
    lower_relief = (
        subduction_bound
        + arc_bound
        + divergence_bound * max(1.0, abs(divergence.axial_depth_multiplier))
        + transform_bound
    )
    upper_relief = (
        max(
            collision_bound * (1.0 + abs(collision.crest_height_multiplier)),
            subduction_bound,
        )
        + arc_bound
        + divergence_bound * max(1.0, abs(divergence.shoulder_height_multiplier))
        + transform_bound
    )
    anomaly = abs(density_variation)
    base_range = (
        -(
            config.basin_depth_percent
            + abs(config.buoyancy.oceanic_height_percent) * anomaly
        )
        * scale,
        (
            config.interior_height_percent
            + abs(config.buoyancy.continental_height_percent) * anomaly
        )
        * scale,
    )
    return (
        (
            base_range[0] - lower_relief,
            base_range[1] + upper_relief + max_shield_height_percent * scale,
        ),
        base_range,
    )
