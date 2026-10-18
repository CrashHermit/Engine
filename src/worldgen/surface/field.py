"""Fixed-footprint terrain measurements sampled from continuous elevation."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.field import ElevationField
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
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fit a local plane and measure sampled relief and detrended roughness."""
    offsets = ring_elevation - center_elevation[:, None]
    mean_offset = np.sum(offsets, axis=1) / (_RING_SAMPLE_COUNT + 1)
    gradient_x = np.sum(offsets * _COSINE_BEARINGS, axis=1) / (4.0 * distance_m)
    gradient_y = np.sum(offsets * _SINE_BEARINGS, axis=1) / (4.0 * distance_m)
    slope_degrees = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))
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
    return slope_degrees, local_relief, roughness


@dataclass(frozen=True, slots=True)
class SurfaceField:
    """Sample surface properties from a retained continuous elevation field."""

    config: SurfaceConfig
    elevation_field: ElevationField

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
        distance_m = self.elevation_field.radius_m * angular_radius
        supplied_center = (
            None
            if center_elevation is None
            else np.asarray(center_elevation, dtype=np.float64)
        )

        for start in range(0, count, _QUERY_BATCH_SIZE):
            end = min(start + _QUERY_BATCH_SIZE, count)
            center_positions = positions[start:end]
            if supplied_center is None:
                center_heights = self.elevation_field.sample(center_positions).elevation
            else:
                center_heights = supplied_center[start:end]

            ring_positions = spherical_ring(
                center_positions, angular_radius, _RING_SAMPLE_COUNT
            )
            ring_heights = self.elevation_field.sample(
                ring_positions.reshape(-1, 3)
            ).elevation.reshape(-1, _RING_SAMPLE_COUNT)
            slope, relief, roughness_values = _neighborhood_metrics(
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
