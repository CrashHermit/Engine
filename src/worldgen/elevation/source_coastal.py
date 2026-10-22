"""Continuous coastal relief driven by regional material influence."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.config import SourceCoastalConfig
from src.worldgen.elevation.profiles import coastal_height_profile
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import noise_multiplier, noise_multiplier_with_gradient
from src.worldgen.utilities.curves import smoothstep


def _smoothstep_gradient(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, 0.0, 1.0)
    return np.where(
        (values > 0.0) & (values < 1.0), 6.0 * clipped * (1.0 - clipped), 0.0
    )


@dataclass(frozen=True, slots=True)
class SourceCoastalSample:
    """Continental influence and its sampled coastal elevation."""

    continental_weight: np.ndarray
    elevation: np.ndarray


@dataclass(frozen=True, slots=True)
class SourceCoastalField:
    """Evaluate coastal relief from a continuous continental-weight field."""

    sample_continental_weight: Callable[[np.ndarray], np.ndarray]
    sample_density_anomaly: Callable[[np.ndarray], np.ndarray]
    span_noise_seeds: tuple[int, int, int]
    config: SourceCoastalConfig = SourceCoastalConfig()
    sample_continental_weight_with_gradient: (
        Callable[[np.ndarray], ScalarSample] | None
    ) = None
    sample_density_anomaly_with_gradient: (
        Callable[[np.ndarray], ScalarSample] | None
    ) = None

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Sample coastal relief and its full Cartesian derivative."""
        query = np.asarray(positions, dtype=np.float64)
        if len(query) == 0:
            return ScalarSample(
                np.empty(0, dtype=np.float64), np.empty((0, 3), dtype=np.float64)
            )
        weight_sample = self.sample_continental_weight_with_gradient(query)
        return self.sample_from_weight_with_gradient(query, weight_sample)

    def sample_from_weight_with_gradient(
        self, positions: np.ndarray, continental_weight: ScalarSample
    ) -> ScalarSample:
        """Evaluate coastal elevation derivatives from sampled material influence."""
        query = np.asarray(positions, dtype=np.float64)
        if len(query) == 0:
            return ScalarSample(
                np.empty(0, dtype=np.float64), np.empty((0, 3), dtype=np.float64)
            )
        density = self.sample_density_anomaly_with_gradient(query)
        profiles = []
        for span_config, seed in zip(
            (self.config.inland, self.config.shelf, self.config.slope),
            self.span_noise_seeds,
            strict=True,
        ):
            noise = noise_multiplier_with_gradient(
                query,
                seed=seed,
                frequency=span_config.noise_frequency,
                strength=span_config.variation_strength,
            )
            profiles.append(
                ScalarSample(
                    span_config.span * noise.values,
                    span_config.span * noise.gradients,
                )
            )
        inland, shelf, slope = profiles
        weight_gradient = continental_weight.gradients
        distance = -continental_weight.values + self.config.coastline_weight
        distance_gradient = -weight_gradient
        inland_input = (distance + inland.values) / inland.values
        inland_input_gradient = (
            (distance_gradient + inland.gradients) * inland.values[:, None]
            - (distance + inland.values)[:, None] * inland.gradients
        ) / inland.values[:, None] ** 2
        shelf_input = distance / shelf.values
        shelf_input_gradient = (
            distance_gradient * shelf.values[:, None]
            - distance[:, None] * shelf.gradients
        ) / shelf.values[:, None] ** 2
        slope_numerator = distance - shelf.values
        slope_input = slope_numerator / slope.values
        slope_input_gradient = (
            (distance_gradient - shelf.gradients) * slope.values[:, None]
            - slope_numerator[:, None] * slope.gradients
        ) / slope.values[:, None] ** 2

        interior = (
            self.config.interior_height_percent
            - self.config.continental_buoyancy_percent * density.values
        ) / 100.0
        interior_gradient = (
            -(self.config.continental_buoyancy_percent / 100.0) * density.gradients
        )
        basin = (
            self.config.basin_depth_percent
            + self.config.oceanic_buoyancy_percent * density.values
        ) / 100.0
        basin_gradient = (
            self.config.oceanic_buoyancy_percent / 100.0
        ) * density.gradients
        inland_profile = smoothstep(inland_input)
        shelf_profile = smoothstep(shelf_input)
        slope_profile = smoothstep(slope_input)
        shelf_depth = self.config.shelf_depth_percent / 100.0
        gradient = (
            interior_gradient * (1.0 - inland_profile)[:, None]
            - interior[:, None]
            * _smoothstep_gradient(inland_input)[:, None]
            * inland_input_gradient
            - shelf_depth
            * _smoothstep_gradient(shelf_input)[:, None]
            * shelf_input_gradient
            - basin_gradient * slope_profile[:, None]
            - (basin - shelf_depth)[:, None]
            * _smoothstep_gradient(slope_input)[:, None]
            * slope_input_gradient
        )
        elevation_values = np.asarray(
            coastal_height_profile(
                continental_weight.values - self.config.coastline_weight + shelf.values,
                inland_width=inland.values,
                shelf_width=shelf.values,
                slope_width=slope.values,
                interior_height=interior,
                shelf_depth=shelf_depth,
                basin_depth=basin,
            ),
            dtype=np.float64,
        )
        return ScalarSample(elevation_values, gradient)

    def sample(self, positions: np.ndarray) -> SourceCoastalSample:
        """Sample material influence, modulated spans, density response, and relief."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(query_points) == 0:
            return self.sample_from_weight(query_points, np.empty(0, dtype=np.float64))
        continental_weight = self.sample_continental_weight(query_points)
        return self.sample_from_weight(query_points, continental_weight)

    def sample_from_weight(
        self, positions: np.ndarray, continental_weight: np.ndarray
    ) -> SourceCoastalSample:
        """Evaluate coastal relief using previously sampled material influence."""
        query_points = np.asarray(positions, dtype=np.float64)
        weight = np.array(continental_weight, dtype=np.float64, copy=True)
        if len(query_points) == 0:
            elevation = np.empty(0, dtype=np.float64)
            weight.setflags(write=False)
            elevation.setflags(write=False)
            return SourceCoastalSample(weight, elevation)

        density_anomaly = self.sample_density_anomaly(query_points)
        inland_span = self.config.inland.span * noise_multiplier(
            query_points,
            seed=self.span_noise_seeds[0],
            frequency=self.config.inland.noise_frequency,
            strength=self.config.inland.variation_strength,
        )
        shelf_span = self.config.shelf.span * noise_multiplier(
            query_points,
            seed=self.span_noise_seeds[1],
            frequency=self.config.shelf.noise_frequency,
            strength=self.config.shelf.variation_strength,
        )
        slope_span = self.config.slope.span * noise_multiplier(
            query_points,
            seed=self.span_noise_seeds[2],
            frequency=self.config.slope.noise_frequency,
            strength=self.config.slope.variation_strength,
        )
        interior_height = (
            self.config.interior_height_percent
            - self.config.continental_buoyancy_percent * density_anomaly
        ) / 100.0
        basin_depth = (
            self.config.basin_depth_percent
            + self.config.oceanic_buoyancy_percent * density_anomaly
        ) / 100.0
        elevation = np.asarray(
            coastal_height_profile(
                weight - self.config.coastline_weight + shelf_span,
                inland_width=inland_span,
                shelf_width=shelf_span,
                slope_width=slope_span,
                interior_height=interior_height,
                shelf_depth=self.config.shelf_depth_percent / 100.0,
                basin_depth=basin_depth,
            ),
            dtype=np.float64,
        )
        weight.setflags(write=False)
        elevation.setflags(write=False)
        return SourceCoastalSample(weight, elevation)

    def sample_elevation(self, positions: np.ndarray) -> np.ndarray:
        """Sample only the scalar relief for generic field composition."""
        return self.sample(positions).elevation
