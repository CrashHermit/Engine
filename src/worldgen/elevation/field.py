"""Retained elevation definitions sampled at arbitrary unit-sphere positions."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.coastal import CoastalField
from src.worldgen.elevation.deformation import TectonicField
from src.worldgen.elevation.impact import ImpactField
from src.worldgen.elevation.model import ElevationResult
from src.worldgen.elevation.variation import TerrainVariationField
from src.worldgen.elevation.volcanism import VolcanicField
from src.worldgen.geometry.boundary import SphericalRegions


@dataclass(frozen=True, slots=True)
class ElevationField:
    """Established geography and source definitions; sampling never regenerates it."""

    radius_m: float
    regions: SphericalRegions
    coastal: CoastalField
    tectonics: TectonicField
    volcanoes: VolcanicField
    impacts: ImpactField
    variation: TerrainVariationField
    elevation_range_fraction: tuple[float, float]
    coastal_elevation_range_fraction: tuple[float, float]

    @property
    def elevation_range_m(self) -> tuple[float, float]:
        return tuple(value * self.radius_m for value in self.elevation_range_fraction)

    @property
    def coastal_elevation_range_m(self) -> tuple[float, float]:
        return tuple(
            value * self.radius_m for value in self.coastal_elevation_range_fraction
        )

    def sample(self, positions: np.ndarray) -> ElevationResult:
        """Return component heights in metres for paired Nx3 unit vectors."""
        positions = np.asarray(positions, dtype=np.float64)
        cells = self.regions.locate(positions)
        coastal = self.coastal.sample(positions, self.radius_m, cell_indices=cells)
        tectonic = self.tectonics.sample(positions, self.radius_m)
        volcanic = self.volcanoes.sample(positions, self.radius_m, cell_indices=cells)
        variation = self.variation.sample(positions, self.radius_m)
        impact = self.impacts.sample(positions, self.radius_m)
        elevation = coastal.elevation + tectonic + volcanic + impact + variation
        for array in (
            coastal.margin_distance,
            coastal.elevation,
            tectonic,
            volcanic,
            impact,
            variation,
            elevation,
        ):
            array.setflags(write=False)
        return ElevationResult(
            coastal_elevation=coastal.elevation,
            tectonic_relief=tectonic,
            volcanic_relief=volcanic,
            impact_relief=impact,
            terrain_variation=variation,
            elevation=elevation,
            margin_distance=coastal.margin_distance,
            crust_boundary_edge_indices=self.coastal.boundary.edge_indices,
            elevation_range_m=self.elevation_range_m,
            coastal_elevation_range_m=self.coastal_elevation_range_m,
        )
