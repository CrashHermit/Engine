"""Retained elevation definitions sampled at arbitrary unit-sphere positions."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.coastal import (
    _base_elevation,
    _sample_width,
    signed_margin_distances,
)
from src.worldgen.elevation.config import ElevationConfig
from src.worldgen.elevation.deformation import TectonicField
from src.worldgen.elevation.model import ElevationResult
from src.worldgen.elevation.volcanism import VolcanicField
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.geology.config import CrustDensityConfig
from src.worldgen.geometry.boundary import BoundaryNetwork, SphericalRegions


@dataclass(frozen=True, slots=True)
class ElevationField:
    """Established geography and source definitions; sampling never regenerates it."""

    config: ElevationConfig
    radius_m: float
    regions: SphericalRegions
    continental_mask: np.ndarray
    crust_boundary: BoundaryNetwork
    plate_boundary: BoundaryNetwork
    density_config: CrustDensityConfig
    density_noise_seed: int
    width_noise_seeds: tuple[int, int, int]
    tectonics: TectonicField
    volcanoes: VolcanicField
    elevation_range_fraction: tuple[float, float]
    base_elevation_range_fraction: tuple[float, float]

    @property
    def elevation_range_m(self) -> tuple[float, float]:
        return tuple(value * self.radius_m for value in self.elevation_range_fraction)

    @property
    def base_elevation_range_m(self) -> tuple[float, float]:
        return tuple(
            value * self.radius_m for value in self.base_elevation_range_fraction
        )

    def sample(self, positions: np.ndarray) -> ElevationResult:
        """Return component heights in metres for paired Nx3 unit vectors."""
        positions = np.asarray(positions, dtype=np.float64)
        cells = self.regions.locate(positions)
        margin = signed_margin_distances(
            positions, self.continental_mask[cells], self.crust_boundary
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
        base = _base_elevation(
            margin,
            self.config,
            self.radius_m,
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
        tectonic = self.tectonics.sample(positions, self.radius_m)
        volcanic = self.volcanoes.sample(positions, self.radius_m)
        elevation = base + tectonic + volcanic
        land_mask = elevation >= 0.0
        for array in (margin, base, tectonic, volcanic, elevation, land_mask):
            array.setflags(write=False)
        return ElevationResult(
            base_elevation=base,
            tectonic_relief=tectonic,
            volcanic_relief=volcanic,
            elevation=elevation,
            margin_distance=margin,
            land_mask=land_mask,
            crust_boundary_edge_indices=self.crust_boundary.edge_indices,
            elevation_range_m=self.elevation_range_m,
            base_elevation_range_m=self.base_elevation_range_m,
        )
