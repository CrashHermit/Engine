"""Fixed-footprint terrain measurements sampled from continuous elevation."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.compose import ScalarSampler
from src.worldgen.field.differential import ScalarGradientSampler
from src.worldgen.geometry.spherical import spherical_ring
from src.worldgen.surface.config import SurfaceConfig
from src.worldgen.surface.model import SurfaceResult

_RING_SAMPLE_COUNT = 8
_QUERY_BATCH_SIZE = 1024
_BEARING_ANGLES = 2.0 * np.pi * np.arange(_RING_SAMPLE_COUNT, dtype=np.float64)
_BEARING_ANGLES /= _RING_SAMPLE_COUNT
_COSINE_BEARINGS = np.cos(_BEARING_ANGLES)
_SINE_BEARINGS = np.sin(_BEARING_ANGLES)
_COSINE_BEARINGS.setflags(write=False)
_SINE_BEARINGS.setflags(write=False)


def _neighborhood_metrics(
    center_elevation: np.ndarray,
    ring_elevation: np.ndarray,
    distance_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Measure sampled relief and roughness after fitting a local plane."""
    offsets = ring_elevation - center_elevation[:, None]
    mean_offset = np.sum(offsets, axis=1) / (_RING_SAMPLE_COUNT + 1)
    gradient_x = np.sum(offsets * _COSINE_BEARINGS, axis=1) / (4.0 * distance_m)
    gradient_y = np.sum(offsets * _SINE_BEARINGS, axis=1) / (4.0 * distance_m)
    local_relief = np.maximum(0.0, np.max(offsets, axis=1)) - np.minimum(
        0.0, np.min(offsets, axis=1)
    )

    center_residual = -mean_offset
    ring_residual = (
        offsets
        - mean_offset[:, None]
        - distance_m
        * (
            gradient_x[:, None] * _COSINE_BEARINGS
            + gradient_y[:, None] * _SINE_BEARINGS
        )
    )
    roughness = np.sqrt(
        (center_residual**2 + np.sum(ring_residual**2, axis=1))
        / (_RING_SAMPLE_COUNT + 1)
    )
    return local_relief, roughness


@dataclass(frozen=True, slots=True)
class SurfaceField:
    """Analytic point slope plus finite-footprint relief and roughness."""

    config: SurfaceConfig
    sample_elevation_meters: ScalarSampler
    radius_m: float
    sample_elevation_meters_with_gradient: ScalarGradientSampler

    def sample(
        self,
        positions: np.ndarray,
        *,
        center_elevation: np.ndarray | None = None,
    ) -> SurfaceResult:
        """Measure surface height and neighborhood shape at unit-sphere positions."""
        positions = np.asarray(positions, dtype=np.float64)
        count = len(positions)
        land_height = np.empty(count, dtype=np.float64)
        water_depth = np.empty(count, dtype=np.float64)
        slope_degrees = np.empty(count, dtype=np.float64)
        local_relief = np.empty(count, dtype=np.float64)
        roughness = np.empty(count, dtype=np.float64)

        angular_radius = self.config.radius_percent * (2.0 * np.pi / 100.0)
        distance_m = self.radius_m * angular_radius
        supplied_center = (
            None
            if center_elevation is None
            else np.asarray(center_elevation, dtype=np.float64)
        )

        for start in range(0, count, _QUERY_BATCH_SIZE):
            end = min(start + _QUERY_BATCH_SIZE, count)
            center_positions = positions[start:end]
            differential = self.sample_elevation_meters_with_gradient(center_positions)
            center_heights = (
                differential.values
                if supplied_center is None
                else supplied_center[start:end]
            )
            tangent_gradient = (
                differential.gradients
                - np.einsum("ni,ni->n", differential.gradients, center_positions)[
                    :, None
                ]
                * center_positions
            )
            slope = np.degrees(
                np.arctan2(
                    np.linalg.norm(tangent_gradient, axis=1),
                    self.radius_m + center_heights,
                )
            )

            ring_positions = spherical_ring(
                center_positions, angular_radius, _RING_SAMPLE_COUNT
            )
            ring_heights = self.sample_elevation_meters(
                ring_positions.reshape(-1, 3)
            ).reshape(-1, _RING_SAMPLE_COUNT)
            relief, roughness_values = _neighborhood_metrics(
                center_heights, ring_heights, distance_m
            )

            land_height[start:end] = np.maximum(center_heights, 0.0)
            water_depth[start:end] = np.maximum(-center_heights, 0.0)
            slope_degrees[start:end] = slope
            local_relief[start:end] = relief
            roughness[start:end] = roughness_values

        for array in (
            land_height,
            water_depth,
            slope_degrees,
            local_relief,
            roughness,
        ):
            array.setflags(write=False)
        return SurfaceResult(
            land_height=land_height,
            water_depth=water_depth,
            slope_degrees=slope_degrees,
            local_relief=local_relief,
            roughness=roughness,
        )

    def sample_normals(self, positions: np.ndarray) -> np.ndarray:
        """Return exact radial-surface normals from the continuous height gradient."""
        directions = np.asarray(positions, dtype=np.float64)
        sample = self.sample_elevation_meters_with_gradient(directions)
        tangent_gradient = (
            sample.gradients
            - np.einsum("ni,ni->n", sample.gradients, directions)[:, None] * directions
        )
        normals = (self.radius_m + sample.values)[
            :, None
        ] * directions - tangent_gradient
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        normals.setflags(write=False)
        return normals
