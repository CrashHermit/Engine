"""Continuous compact influence fields for volumetric Voronoi boundaries."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.falloff import compact_influence
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.field.warp import ShearWarpField
from src.worldgen.geometry.voronoi import (
    VoronoiBoundaryGeometry,
    build_voronoi_boundary_geometry,
    voronoi_boundary_distances,
)


@dataclass(frozen=True, slots=True)
class BoundaryInfluenceConfig:
    """Source-coordinate width for the compact influence around each face."""

    width: float


@dataclass(frozen=True, slots=True)
class VoronoiBoundarySample:
    """Per-pair boundary influence values at paired XYZ query positions."""

    region_pairs: np.ndarray
    influence: np.ndarray


@dataclass(frozen=True, slots=True)
class VoronoiBoundaryField:
    """A continuously sampled, warped Voronoi boundary influence field."""

    warp: ShearWarpField
    geometry: VoronoiBoundaryGeometry
    config: BoundaryInfluenceConfig

    def sample(self, positions: np.ndarray) -> VoronoiBoundarySample:
        """Return independent compact influence values for all valid faces."""
        warped_positions = self.warp.sample(positions)
        face_count = len(self.geometry.faces)
        influence = np.empty((len(warped_positions), face_count), dtype=np.float64)

        for start in range(0, len(warped_positions), 1024):
            stop = min(start + 1024, len(warped_positions))
            distances = voronoi_boundary_distances(
                warped_positions[start:stop], self.geometry
            )
            influence[start:stop] = compact_influence(
                distances, width=self.config.width
            )

        influence.setflags(write=False)
        return VoronoiBoundarySample(
            region_pairs=self.geometry.region_pairs,
            influence=influence,
        )


def build_voronoi_boundary_field(
    regions: WarpedVoronoiField,
    config: BoundaryInfluenceConfig,
) -> VoronoiBoundaryField:
    """Build face geometry once, reusing a warped partition's seeds and warp."""
    geometry = build_voronoi_boundary_geometry(regions.voronoi.seeds)
    return VoronoiBoundaryField(warp=regions.warp, geometry=geometry, config=config)
