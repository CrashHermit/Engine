"""Continuous sampling of seed-anchored rigid region motion."""

import numpy as np

from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.geometry.rotation import rotation_vectors
from src.worldgen.geology.config import PlateMotionConfig


def generate_plate_motion(
    seeds: np.ndarray,
    config: PlateMotionConfig,
    *,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate read-only angular velocities along the original seed axes.

    An original seed at the Cartesian origin cannot define a rotation axis and
    raises ``ValueError``. Nonzero seeds, including arbitrarily small ones, are
    normalized by the rotation-vector primitive without jitter or a cutoff.
    """
    speeds = rng.uniform(
        config.min_angular_speed,
        config.max_angular_speed,
        size=len(seeds),
    )
    angular_velocity = rotation_vectors(seeds, speeds)
    angular_velocity.setflags(write=False)
    return angular_velocity


def build_plate_motion_field(
    regions: WarpedVoronoiField,
    config: PlateMotionConfig,
    *,
    rng: np.random.Generator,
) -> RegionRotationField:
    """Compose region ownership with one generated rotation per original seed."""
    angular_velocity = generate_plate_motion(regions.voronoi.seeds, config, rng=rng)
    return RegionRotationField(regions=regions, angular_velocity=angular_velocity)
