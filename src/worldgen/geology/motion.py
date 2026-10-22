"""Continuous rigid region motion with geometry-independent Euler axes."""

import numpy as np

from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.seeds import generate_direction_seeds
from src.worldgen.geometry.rotation import rotation_vectors
from src.worldgen.geology.config import PlateMotionConfig


def generate_plate_motion(
    seeds: np.ndarray,
    config: PlateMotionConfig,
    *,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate independent isotropic Euler axes and configured angular speeds.

    Seed positions determine only the region count, never the motion axes.
    The injected motion RNG is independent of partition generation.
    """
    speeds = rng.uniform(
        config.min_angular_speed,
        config.max_angular_speed,
        size=len(seeds),
    )
    axes = generate_direction_seeds(len(seeds), rng=rng)
    angular_velocity = rotation_vectors(axes, speeds)
    angular_velocity.setflags(write=False)
    return angular_velocity


def build_plate_motion_field(
    partition: VoronoiField3D,
    config: PlateMotionConfig,
    *,
    rng: np.random.Generator,
) -> RegionRotationField:
    """Compose source ownership with one generated rotation per partition seed."""
    angular_velocity = generate_plate_motion(partition.seeds, config, rng=rng)
    return RegionRotationField(partition=partition, angular_velocity=angular_velocity)
