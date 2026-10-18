"""Continuous additive meteor-impact relief on the unit sphere."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.config import ImpactConfig
from src.worldgen.elevation.profiles import impact_profile
from src.worldgen.geometry.spherical import angular_distances


@dataclass(frozen=True, slots=True)
class ImpactField:
    """Retained impact sources sampled continuously at spherical positions."""

    config: ImpactConfig
    centers: np.ndarray
    radii_percent: np.ndarray
    depths_percent: np.ndarray
    sharpnesses: np.ndarray

    def __post_init__(self) -> None:
        for array in (
            self.centers,
            self.radii_percent,
            self.depths_percent,
            self.sharpnesses,
        ):
            array.setflags(write=False)

    def sample(self, positions: np.ndarray, radius_m: float) -> np.ndarray:
        """Return the additive crater relief at paired unit-sphere positions."""
        relief = np.zeros(len(positions), dtype=np.float64)
        if not len(positions) or not len(self.centers):
            return relief
        for center, radius, depth, sharpness in zip(
            self.centers,
            self.radii_percent,
            self.depths_percent,
            self.sharpnesses,
        ):
            distances = angular_distances(
                positions, np.broadcast_to(center, positions.shape)
            ) * (100.0 / (2.0 * np.pi))
            support_radius = radius * (1.0 + self.config.ejecta_width_fraction)
            support = distances <= support_radius
            relief[support] += impact_profile(
                distances[support],
                float(radius),
                float(sharpness),
                self.config.rim_height_fraction,
                self.config.ejecta_width_fraction,
            ) * (float(depth) * radius_m / 100.0)
        return relief

    def bounds(self, radius_m: float) -> tuple[float, float]:
        """Return query-independent conservative bounds including overlap."""
        depth_sum = float(np.sum(self.depths_percent)) * radius_m / 100.0
        return (
            -depth_sum,
            self.config.rim_height_fraction * depth_sum,
        )


def generate_impact_field(
    config: ImpactConfig, *, rng: np.random.Generator
) -> ImpactField:
    """Generate independent continuous source locations and profile parameters."""
    z = rng.uniform(-1.0, 1.0, size=config.count)
    longitude = rng.uniform(0.0, 2.0 * np.pi, size=config.count)
    planar_radius = np.sqrt(1.0 - z * z)
    centers = np.column_stack(
        (planar_radius * np.cos(longitude), planar_radius * np.sin(longitude), z)
    )
    radii_percent = (
        config.min_radius_percent
        + (config.max_radius_percent - config.min_radius_percent)
        * rng.random(config.count) ** 2
    )
    depths_percent = config.min_depth_percent + (
        config.max_depth_percent - config.min_depth_percent
    ) * rng.random(config.count)
    sharpnesses = config.min_sharpness + (
        config.max_sharpness - config.min_sharpness
    ) * rng.random(config.count)
    return ImpactField(
        config=config,
        centers=centers,
        radii_percent=radii_percent,
        depths_percent=depths_percent,
        sharpnesses=sharpnesses,
    )
