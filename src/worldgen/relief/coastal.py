"""Continuous coastal relief driven by regional material influence."""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import noise_multiplier, noise_multiplier_with_gradient
from src.worldgen.utilities.curves import smoothstep, smoothstep_derivative


@dataclass(frozen=True, slots=True)
class SourceCoastalSpanConfig:
    """Dimensionless coastal span and independent procedural modulation."""

    influence_span: float
    variation_strength: float = 0.3
    noise_frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class SourceCoastalConfig:
    """Coastal relief heights and density responses as percentages of radius."""

    coastline_weight: float = 0.65
    inland: SourceCoastalSpanConfig = field(
        default_factory=lambda: SourceCoastalSpanConfig(0.2)
    )
    shelf: SourceCoastalSpanConfig = field(
        default_factory=lambda: SourceCoastalSpanConfig(0.15)
    )
    slope: SourceCoastalSpanConfig = field(
        default_factory=lambda: SourceCoastalSpanConfig(0.25)
    )
    interior_height_percent: float = 0.0094
    shelf_depth_percent: float = 0.0031
    # About 4 km at the reference radius; separate from trench relief.
    basin_depth_percent: float = 0.0628
    continental_buoyancy_percent: float = 0.0157
    oceanic_buoyancy_percent: float = 0.0314


def coastal_height_profile(
    margin_distance: np.ndarray,
    *,
    inland_width: np.ndarray,
    shelf_width: np.ndarray,
    slope_width: np.ndarray,
    interior_height: np.ndarray | float,
    shelf_depth: np.ndarray | float,
    basin_depth: np.ndarray | float,
) -> np.ndarray:
    """Return relief from a material-influence coordinate and profile widths."""
    distance = shelf_width - margin_distance
    inland = smoothstep((distance + inland_width) / inland_width)
    shelf = smoothstep(distance / shelf_width)
    slope = smoothstep((distance - shelf_width) / slope_width)
    return (
        interior_height * (1.0 - inland)
        - shelf_depth * shelf
        - (basin_depth - shelf_depth) * slope
    )


def coastal_height_profile_with_partials(
    margin_distance: np.ndarray,
    *,
    inland_width: np.ndarray,
    shelf_width: np.ndarray,
    slope_width: np.ndarray,
    interior_height: np.ndarray | float,
    shelf_depth: np.ndarray | float,
    basin_depth: np.ndarray | float,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Return coastal relief and partials by its seven independent inputs."""
    distance = shelf_width - margin_distance
    inland_input = (distance + inland_width) / inland_width
    shelf_input = distance / shelf_width
    slope_input = (distance - shelf_width) / slope_width
    inland = smoothstep(inland_input)
    shelf = smoothstep(shelf_input)
    slope = smoothstep(slope_input)
    inland_slope = smoothstep_derivative(inland_input)
    shelf_slope = smoothstep_derivative(shelf_input)
    slope_slope = smoothstep_derivative(slope_input)
    value = (
        interior_height * (1.0 - inland)
        - shelf_depth * shelf
        - (basin_depth - shelf_depth) * slope
    )
    d_margin = (
        interior_height * inland_slope / inland_width
        + shelf_depth * shelf_slope / shelf_width
        + (basin_depth - shelf_depth) * slope_slope / slope_width
    )
    d_inland_width = interior_height * inland_slope * distance / inland_width**2
    d_shelf_width = (
        -interior_height * inland_slope / inland_width
        - shelf_depth * shelf_slope * margin_distance / shelf_width**2
    )
    d_slope_width = (
        -(basin_depth - shelf_depth) * slope_slope * margin_distance / slope_width**2
    )
    d_interior_height = 1.0 - inland
    d_shelf_depth = slope - shelf
    d_basin_depth = -slope
    return (
        value,
        d_margin,
        d_inland_width,
        d_shelf_width,
        d_slope_width,
        d_interior_height,
        d_shelf_depth,
        d_basin_depth,
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
    influence_span_noise_seeds: tuple[int, int, int]
    sample_continental_weight_with_gradient: Callable[[np.ndarray], ScalarSample]
    sample_density_anomaly_with_gradient: Callable[[np.ndarray], ScalarSample]
    config: SourceCoastalConfig = SourceCoastalConfig()

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
            self.influence_span_noise_seeds,
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
                    span_config.influence_span * noise.values,
                    span_config.influence_span * noise.gradients,
                )
            )
        inland, shelf, slope = profiles
        weight_gradient = continental_weight.gradients
        margin_distance = (
            continental_weight.values - self.config.coastline_weight + shelf.values
        )
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
        shelf_depth = self.config.shelf_depth_percent / 100.0
        (
            elevation_values,
            d_margin,
            d_inland_width,
            d_shelf_width,
            d_slope_width,
            d_interior_height,
            _,
            d_basin_depth,
        ) = coastal_height_profile_with_partials(
            margin_distance,
            inland_width=inland.values,
            shelf_width=shelf.values,
            slope_width=slope.values,
            interior_height=interior,
            shelf_depth=shelf_depth,
            basin_depth=basin,
        )
        gradient = (
            d_margin[:, None] * (weight_gradient + shelf.gradients)
            + d_inland_width[:, None] * inland.gradients
            + d_shelf_width[:, None] * shelf.gradients
            + d_slope_width[:, None] * slope.gradients
            + d_interior_height[:, None] * interior_gradient
            + d_basin_depth[:, None] * basin_gradient
        )
        return ScalarSample(np.asarray(elevation_values, dtype=np.float64), gradient)

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
        inland_span = self.config.inland.influence_span * noise_multiplier(
            query_points,
            seed=self.influence_span_noise_seeds[0],
            frequency=self.config.inland.noise_frequency,
            strength=self.config.inland.variation_strength,
        )
        shelf_span = self.config.shelf.influence_span * noise_multiplier(
            query_points,
            seed=self.influence_span_noise_seeds[1],
            frequency=self.config.shelf.noise_frequency,
            strength=self.config.shelf.variation_strength,
        )
        slope_span = self.config.slope.influence_span * noise_multiplier(
            query_points,
            seed=self.influence_span_noise_seeds[2],
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
