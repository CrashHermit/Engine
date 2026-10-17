"""Retained spherical volcanic shields with continuous plate-edge tapering."""

import numpy as np

from src.worldgen.elevation.profiles import shield_profile
from src.worldgen.geology.model import HotspotResult, VolcanoSites
from src.worldgen.geometry.boundary import BoundaryNetwork, SphericalRegions
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.spherical import angular_distances
from src.worldgen.utilities.curves import smoothstep


class VolcanicField:
    """Static shield geometry; eruption state never removes an existing landform."""

    def __init__(
        self,
        mesh: Mesh,
        plate_ids: np.ndarray,
        hotspots: HotspotResult,
        sites: VolcanoSites,
        regions: SphericalRegions,
    ) -> None:
        historical = sites.heights_percent > 0.0
        cells = np.concatenate((hotspots.seed_indices, sites.cell_indices[historical]))
        self.centers = mesh.vertices[cells].copy()
        self.plates = plate_ids[cells].copy()
        self.widths_percent = np.concatenate(
            (hotspots.widths_percent, sites.widths_percent[historical])
        )
        self.heights_percent = np.concatenate(
            (hotspots.heights_percent, sites.heights_percent[historical])
        )
        self.regions = regions
        self.plate_ids = plate_ids
        self.boundaries = {}
        self.center_tapers = np.ones(len(cells), dtype=np.float64)
        for plate in np.unique(self.plates):
            membership = plate_ids == plate
            boundary = BoundaryNetwork(mesh, membership)
            self.boundaries[int(plate)] = boundary
            source_ids = np.flatnonzero(self.plates == plate)
            distances, _, _ = boundary.nearest(self.centers[source_ids])
            self.center_tapers[source_ids] = smoothstep(
                distances / self.widths_percent[source_ids]
            )
        for array in (
            self.centers,
            self.plates,
            self.widths_percent,
            self.heights_percent,
            self.center_tapers,
        ):
            array.setflags(write=False)

    def sample(self, positions: np.ndarray, radius_m: float) -> np.ndarray:
        """Sample compact shields, vanishing continuously at their plate edges."""
        relief = np.zeros(len(positions), dtype=np.float64)
        if not len(positions) or not len(self.centers):
            return relief
        plates = self.plate_ids[self.regions.locate(positions)]
        for center, plate, width, height, center_taper in zip(
            self.centers,
            self.plates,
            self.widths_percent,
            self.heights_percent,
            self.center_tapers,
        ):
            if width <= 0.0 or height <= 0.0:
                continue
            distances = angular_distances(
                positions, np.broadcast_to(center, positions.shape)
            ) * (100.0 / (2.0 * np.pi))
            support = (plates == plate) & (distances < width)
            taper = np.minimum(
                smoothstep(
                    self.boundaries[int(plate)].nearest(positions[support])[0] / width
                )
                / center_taper,
                1.0,
            )
            response = np.zeros(len(positions), dtype=np.float64)
            response[support] = shield_profile(distances[support], float(width)) * taper
            response *= radius_m * float(height) / 100.0
            np.maximum(relief, response, out=relief)
        return relief
