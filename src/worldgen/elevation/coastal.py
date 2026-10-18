"""Coastal elevation calculations shared by the elevation generator."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.config import CoastalConfig, CoastalWidthConfig
from src.worldgen.elevation.model import CoastalResult
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.geology.config import CrustDensityConfig
from src.worldgen.geometry.boundary import BoundaryNetwork
from src.worldgen.utilities.curves import smoothstep


@dataclass(frozen=True, slots=True)
class CoastalField:
    """Continuous coastal contribution over established crust geography."""

    config: CoastalConfig
    continental_mask: np.ndarray
    boundary: BoundaryNetwork
    density_config: CrustDensityConfig
    density_noise_seed: int
    width_noise_seeds: tuple[int, int, int]

    def sample(
        self,
        positions: np.ndarray,
        radius_m: float,
        *,
        cell_indices: np.ndarray,
    ) -> CoastalResult:
        margin = signed_margin_distances(
            positions, self.continental_mask[cell_indices], self.boundary
        )
        density_anomaly = (
            noise_multiplier(
                positions,
                seed=self.density_noise_seed,
                frequency=self.density_config.noise_frequency,
                strength=self.density_config.variation_strength,
            )
            - 1.0
        )
        elevation = coastal_profile(
            margin,
            self.config,
            radius_m,
            density_anomaly=density_anomaly,
            inland_width=_sample_width(
                positions, self.config.inland, noise_seed=self.width_noise_seeds[0]
            ),
            shelf_width=_sample_width(
                positions, self.config.shelf, noise_seed=self.width_noise_seeds[1]
            ),
            slope_width=_sample_width(
                positions, self.config.slope, noise_seed=self.width_noise_seeds[2]
            ),
        )
        return CoastalResult(elevation=elevation, margin_distance=margin)


def signed_margin_distances(
    positions: np.ndarray,
    continental_mask: np.ndarray,
    boundary: BoundaryNetwork,
) -> np.ndarray:
    """Return signed exact spherical distance to the established crust margin."""
    distances, _, _ = boundary.nearest(positions)
    return np.where(continental_mask, distances, -distances)


def _sample_width(
    positions: np.ndarray, config: CoastalWidthConfig, *, noise_seed: int
) -> np.ndarray:
    """Sample broad, continuous width variation without sample-set normalization."""
    return config.base_percent * noise_multiplier(
        positions,
        seed=noise_seed,
        frequency=config.noise_frequency,
        strength=config.variation_strength,
    )


def coastal_profile(
    margin_distance: np.ndarray,
    config: CoastalConfig,
    radius_m: float,
    *,
    density_anomaly: np.ndarray,
    inland_width: np.ndarray,
    shelf_width: np.ndarray,
    slope_width: np.ndarray,
) -> np.ndarray:
    """Apply the saturated smooth coastal profile to signed margin distance."""
    distance = shelf_width - margin_distance
    inland = smoothstep((distance + inland_width) / inland_width)
    shelf = smoothstep(distance / shelf_width)
    slope = smoothstep((distance - shelf_width) / slope_width)
    interior_target = (
        config.interior_height_percent
        - config.buoyancy.continental_height_percent * density_anomaly
    )
    basin_target = (
        config.basin_depth_percent
        + config.buoyancy.oceanic_height_percent * density_anomaly
    )
    return (
        interior_target * (1.0 - inland)
        - config.shelf_depth_percent * shelf
        - (basin_target - config.shelf_depth_percent) * slope
    ) * (radius_m / 100.0)
