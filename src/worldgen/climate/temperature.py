"""Analytic latitude-temperature baseline over Cartesian axial coordinates."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.axis import AxialCoordinateField
from src.worldgen.field.differential import ScalarSample


@dataclass(frozen=True, slots=True)
class TemperatureConfig:
    """Celsius baseline at the unit-sphere equator and poles."""

    equator_temperature_c: float = 30.0
    pole_temperature_c: float = -20.0


@dataclass(frozen=True, slots=True)
class LatitudeTemperatureField:
    """Quadratic axial temperature, calibrated at the unit equator and poles."""

    axis: AxialCoordinateField
    config: TemperatureConfig

    def sample_from_axis(self, axial_coordinate: np.ndarray) -> np.ndarray:
        """Evaluate Celsius temperatures from previously sampled axial coordinates."""
        axial = np.asarray(axial_coordinate, dtype=np.float64)
        difference = self.config.equator_temperature_c - self.config.pole_temperature_c
        values = self.config.equator_temperature_c - difference * axial * axial
        values.setflags(write=False)
        return values

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample the unwarped volumetric baseline without normalizing positions."""
        return self.sample_from_axis(self.axis.sample(positions))

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Return Celsius temperatures and analytic Cartesian gradients."""
        axial = self.axis.sample_with_gradient(positions)
        difference = self.config.equator_temperature_c - self.config.pole_temperature_c
        gradients = (-2.0 * difference * axial.values)[:, None] * axial.gradients
        return ScalarSample(self.sample_from_axis(axial.values), gradients)
