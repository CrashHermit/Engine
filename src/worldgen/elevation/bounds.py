"""Conservative elevation ranges from retained source and noise definitions."""

from src.worldgen.elevation.config import (
    CoastalConfig,
    DeformationConfig,
    ElevationConfig,
)


def coastal_bounds(
    config: CoastalConfig,
    radius_m: float,
    *,
    density_variation: float,
) -> tuple[float, float]:
    """Bound the coastal profile's saturated targets and density response."""
    scale = radius_m / 100.0
    anomaly = abs(density_variation)
    return (
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


def tectonic_bounds(
    config: DeformationConfig,
    radius_m: float,
    *,
    max_motion: float,
) -> tuple[float, float]:
    """Bound the combined tectonic relief envelopes and signed profiles."""
    collision = config.collision
    subduction = config.subduction
    divergence = config.divergence
    scale = radius_m / 100.0
    collision_bound = abs(collision.height_percent) * scale * max_motion
    subduction_bound = abs(subduction.height_percent) * scale * max_motion
    trench_bound = subduction_bound * max(1.0, abs(subduction.trench_depth_multiplier))
    arc_bound = (
        subduction_bound
        * abs(subduction.arc_height_multiplier)
        * (1.0 + abs(subduction.arc_variation_strength))
    )
    divergence_bound = abs(divergence.height_percent) * scale * max_motion
    # |normal|*shear/(|normal|+shear) <= (|normal|+shear)/4 <= max_motion/2.
    transform_bound = abs(config.transform.height_percent) * scale * max_motion / 2.0
    lower_relief = (
        trench_bound
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
    return -lower_relief, upper_relief


def elevation_bounds(
    config: ElevationConfig,
    radius_m: float,
    *,
    density_variation: float,
    max_motion: float,
    max_shield_height_percent: float,
    impact_range: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Compose conservative contribution bounds, independent of query samples."""
    coastal_range = coastal_bounds(
        config.coastal, radius_m, density_variation=density_variation
    )
    tectonic_range = tectonic_bounds(
        config.deformation, radius_m, max_motion=max_motion
    )
    scale = radius_m / 100.0
    variation_bound = abs(config.variation.amplitude_percent) * scale
    return (
        (
            coastal_range[0] + tectonic_range[0] + impact_range[0] - variation_bound,
            coastal_range[1]
            + tectonic_range[1]
            + impact_range[1]
            + max_shield_height_percent * scale
            + variation_bound,
        ),
        coastal_range,
    )
