"""Static origin-based rod scalar fields in Cartesian source coordinates."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.compose import ScalarSampler
from src.worldgen.field.differential import ScalarSample, ScalarGradientSampler
from src.worldgen.utilities.curves import smoothstep


def _smoothstep_derivative(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, 0.0, 1.0)
    return np.where(
        (values > 0.0) & (values < 1.0), 6.0 * clipped * (1.0 - clipped), 0.0
    )


def _rod_relief_with_gradient(
    points: np.ndarray,
    direction: np.ndarray,
    *,
    width: np.ndarray,
    length: np.ndarray,
    height: np.ndarray,
    width_gradient: np.ndarray,
    length_gradient: np.ndarray,
    height_gradient: np.ndarray,
    taper_fraction: float,
    profile_power: float,
) -> tuple[np.ndarray, np.ndarray]:
    axial = np.einsum("ij,j->i", points, direction)
    axial_gradient = np.broadcast_to(direction, points.shape)
    squared_norms = np.einsum("ij,ij->i", points, points)
    radial_squared = np.maximum(squared_norms - axial * axial, 0.0)
    radial_squared_gradient = 2.0 * (points - axial[:, None] * direction)

    radial_base = np.maximum(1.0 - radial_squared / width**2, 0.0)
    radial = radial_base**profile_power
    radial_active = radial_base > 0.0
    radial_gradient = np.zeros_like(points)
    if profile_power != 0.0:
        radial_gradient += (
            -profile_power
            * radial_base[:, None] ** (profile_power - 1.0)
            * radial_squared_gradient
            / width[:, None] ** 2
        ) * radial_active[:, None]
        radial_gradient += (
            2.0
            * profile_power
            * radial_base[:, None] ** (profile_power - 1.0)
            * radial_squared[:, None]
            * width_gradient
            / width[:, None] ** 3
        ) * radial_active[:, None]

    taper_width = length * taper_fraction
    start_input = axial / taper_width
    end_input = (length - axial) / taper_width
    start_gate = smoothstep(start_input)
    end_gate = smoothstep(end_input)
    axial_gate = start_gate * end_gate
    start_gradient = _smoothstep_derivative(start_input)[:, None] * (
        axial_gradient / taper_width[:, None]
        - axial[:, None] * length_gradient / (taper_width[:, None] * length[:, None])
    )
    end_gradient = _smoothstep_derivative(end_input)[:, None] * (
        (length_gradient - axial_gradient) / taper_width[:, None]
        - (length - axial)[:, None]
        * length_gradient
        / (taper_width[:, None] * length[:, None])
    )
    axial_gate_gradient = (
        start_gradient * end_gate[:, None] + end_gradient * start_gate[:, None]
    )
    values = height * radial * axial_gate
    gradients = height_gradient * (radial * axial_gate)[:, None] + height[:, None] * (
        radial_gradient * axial_gate[:, None] + radial[:, None] * axial_gate_gradient
    )
    return values, gradients


def rod_relief(
    axial: np.ndarray,
    radial_squared: np.ndarray,
    *,
    width: float | np.ndarray,
    length: float | np.ndarray,
    height: float | np.ndarray,
    taper_fraction: float = 0.1,
    profile_power: float = 2.0,
) -> np.ndarray:
    """Evaluate a compact radial mound with smoothly tapered axial ends."""
    axial = np.asarray(axial, dtype=np.float64)
    radial_squared = np.asarray(radial_squared, dtype=np.float64)
    radial = (
        np.maximum(1.0 - radial_squared / (np.asarray(width) ** 2), 0.0)
        ** profile_power
    )
    axial_gate = smoothstep(axial / (np.asarray(length) * taper_fraction))
    axial_gate *= smoothstep(
        (np.asarray(length) - axial) / (np.asarray(length) * taper_fraction)
    )
    return np.asarray(height) * radial * axial_gate


@dataclass(frozen=True, slots=True)
class RodScalarField:
    """Additive scalar field formed by finite rods extending from the origin."""

    directions: np.ndarray
    widths: np.ndarray
    lengths: np.ndarray
    heights: np.ndarray
    taper_fraction: float = 0.1
    profile_power: float = 2.0
    sample_width_multiplier: ScalarSampler | None = None
    sample_length_multiplier: ScalarSampler | None = None
    sample_height_multiplier: ScalarSampler | None = None
    sample_width_multiplier_gradient: ScalarGradientSampler | None = None
    sample_length_multiplier_gradient: ScalarGradientSampler | None = None
    sample_height_multiplier_gradient: ScalarGradientSampler | None = None

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Evaluate rod relief and its exact Cartesian gradient."""
        query = np.asarray(positions, dtype=np.float64)
        count = len(query)
        values = np.zeros(count, dtype=np.float64)
        gradients = np.zeros((count, 3), dtype=np.float64)
        if count == 0 or len(self.directions) == 0:
            return ScalarSample(values, gradients)

        multipliers = []
        for value_sampler, gradient_sampler in (
            (self.sample_width_multiplier, self.sample_width_multiplier_gradient),
            (self.sample_length_multiplier, self.sample_length_multiplier_gradient),
            (self.sample_height_multiplier, self.sample_height_multiplier_gradient),
        ):
            if value_sampler is None:
                multipliers.append(
                    ScalarSample(
                        np.ones(count, dtype=np.float64),
                        np.zeros((count, 3), dtype=np.float64),
                    )
                )
            else:
                multipliers.append(gradient_sampler(query))
        width_multiplier, length_multiplier, height_multiplier = multipliers
        for index, direction in enumerate(self.directions):
            rod_values, rod_gradients = _rod_relief_with_gradient(
                query,
                direction,
                width=self.widths[index] * width_multiplier.values,
                length=self.lengths[index] * length_multiplier.values,
                height=self.heights[index] * height_multiplier.values,
                width_gradient=self.widths[index] * width_multiplier.gradients,
                length_gradient=self.lengths[index] * length_multiplier.gradients,
                height_gradient=self.heights[index] * height_multiplier.gradients,
                taper_fraction=self.taper_fraction,
                profile_power=self.profile_power,
            )
            values += rod_values
            gradients += rod_gradients
        return ScalarSample(values, gradients)

    def __post_init__(self) -> None:
        directions = np.array(self.directions, dtype=np.float64, copy=True)
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        directions.setflags(write=False)
        object.__setattr__(self, "directions", directions)
        for name in ("widths", "lengths", "heights"):
            values = np.array(getattr(self, name), dtype=np.float64, copy=True)
            values.setflags(write=False)
            object.__setattr__(self, name, values)

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Evaluate all rods at the supplied unnormalized Cartesian positions."""
        query = np.asarray(positions, dtype=np.float64)
        count = len(query)
        values = np.zeros(count, dtype=np.float64)
        if count == 0 or len(self.directions) == 0:
            values.setflags(write=False)
            return values

        width_multiplier = (
            self.sample_width_multiplier(query)
            if self.sample_width_multiplier is not None
            else 1.0
        )
        length_multiplier = (
            self.sample_length_multiplier(query)
            if self.sample_length_multiplier is not None
            else 1.0
        )
        height_multiplier = (
            self.sample_height_multiplier(query)
            if self.sample_height_multiplier is not None
            else 1.0
        )
        squared_norms = np.einsum("ij,ij->i", query, query)
        for index, direction in enumerate(self.directions):
            # Fixed three-component reduction avoids BLAS layout/batch rounding.
            axial = np.einsum("ij,j->i", query, direction)
            radial_squared = np.maximum(squared_norms - axial * axial, 0.0)
            values += rod_relief(
                axial,
                radial_squared,
                width=self.widths[index] * width_multiplier,
                length=self.lengths[index] * length_multiplier,
                height=self.heights[index] * height_multiplier,
                taper_fraction=self.taper_fraction,
                profile_power=self.profile_power,
            )
        values.setflags(write=False)
        return values
