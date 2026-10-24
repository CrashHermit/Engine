"""Continuous Cartesian zonal-band and wind fields."""

from dataclasses import dataclass

import numpy as np


from src.worldgen.climate.model import CirculationSample
from src.worldgen.field.axis import AxialCoordinateField
from src.worldgen.field.differential import ScalarSample, VectorSample
from src.worldgen.field.motion import RotationField
from src.worldgen.geometry.vector import (
    regularized_normalize,
    regularized_normalize_with_jacobian,
)


@dataclass(frozen=True, slots=True)
class CirculationConfig:
    """Reference wind speed and smooth calm-region width around the axis."""

    base_speed_m_s: float = 10.0
    axis_calm_radius_percent: float = 5.0


@dataclass(frozen=True, slots=True)
class CirculationBandField:
    """Signed cosine circulation wave over the squared Cartesian axial coordinate."""

    axis: AxialCoordinateField

    def sample_from_axis(self, axial_coordinate: np.ndarray) -> np.ndarray:
        """Evaluate band strength from already sampled linear axial coordinates."""
        z = np.asarray(axial_coordinate, dtype=np.float64)
        result = -np.cos(2.0 * np.pi * z * z)
        result.setflags(write=False)
        return result

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample scalar band strength at arbitrary Cartesian positions."""
        return self.sample_from_axis(self.axis.sample(positions))

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Sample bands and their Cartesian analytic gradients."""
        axial = self.axis.sample_with_gradient(positions)
        z = axial.values
        phase = 2.0 * np.pi * z * z
        values = -np.cos(phase)
        derivative_z = 4.0 * np.pi * z * np.sin(phase)
        gradients = derivative_z[:, None] * axial.gradients
        return ScalarSample(values, gradients)


@dataclass(frozen=True, slots=True)
class ZonalWindField:
    """Regularized Cartesian circulation whose strength follows zonal bands."""

    rotation: RotationField
    bands: CirculationBandField
    base_speed_m_s: float
    axis_calm_radius: float

    def sample_from_band(
        self, positions: np.ndarray, band_strength: np.ndarray
    ) -> np.ndarray:
        """Compose supplied band strengths with the regularized rotation field."""
        points = np.asarray(positions, dtype=np.float64)
        bands = np.asarray(band_strength, dtype=np.float64)
        rotational = self.rotation.sample(points)
        values = regularized_normalize(
            rotational,
            self.axis_calm_radius,
            multiplier=self.base_speed_m_s * bands[:, None],
        )
        values.setflags(write=False)
        return values

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample Cartesian winds at arbitrary positions."""
        points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_band(points, self.bands.sample(points))

    def sample_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        """Sample winds and their exact analytic Cartesian Jacobians."""
        points = np.asarray(positions, dtype=np.float64)
        band_sample = self.bands.sample_with_gradient(points)
        rotation_sample = self.rotation.sample_with_jacobian(points)
        rotational = rotation_sample.values
        regularized, regularized_jacobian = regularized_normalize_with_jacobian(
            rotational, self.axis_calm_radius
        )
        values = self.base_speed_m_s * band_sample.values[:, None] * regularized
        jacobians = self.base_speed_m_s * (
            band_sample.values[:, None, None]
            * np.einsum("nij,njk->nik", regularized_jacobian, rotation_sample.jacobians)
            + regularized[:, :, None] * band_sample.gradients[:, None, :]
        )
        return VectorSample(values, jacobians)


@dataclass(frozen=True, slots=True)
class CirculationField:
    """Shared-axis circulation sampler with scalar bands and Cartesian winds."""

    axis: AxialCoordinateField
    bands: CirculationBandField
    wind: ZonalWindField

    def sample(self, positions: np.ndarray) -> CirculationSample:
        """Sample axial coordinates, bands, and winds while sharing intermediates."""
        points = np.asarray(positions, dtype=np.float64)
        axial = self.axis.sample(points)
        bands = self.bands.sample_from_axis(axial)
        winds = self.wind.sample_from_band(points, bands)
        return CirculationSample(axial, bands, winds)
