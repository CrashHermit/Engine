"""Static origin-based rod scalar fields in Cartesian coordinates."""

from dataclasses import dataclass

import numpy as np
from numba import njit, prange
from numba.extending import register_jitable

from src.worldgen.field.compose import ScalarSampler
from src.worldgen.field.differential import ScalarSample, ScalarGradientSampler
from src.worldgen.utilities.curves import (
    smoothstep,
    smoothstep_derivative,
    smoothstep_scalar,
    smoothstep_derivative_scalar,
)


def rod_coordinates(
    positions: np.ndarray, direction: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return axial and squared radial coordinates for origin-based rods."""
    axial = np.einsum("ij,j->i", positions, direction)
    squared_norms = np.einsum("ij,ij->i", positions, positions)
    radial_squared = np.maximum(squared_norms - axial * axial, 0.0)
    return axial, radial_squared


def rod_coordinates_with_gradient(
    positions: np.ndarray, direction: np.ndarray
) -> tuple[ScalarSample, ScalarSample]:
    """Return rod coordinates and their Cartesian gradients."""
    axial, radial_squared = rod_coordinates(positions, direction)
    axial_gradient = np.broadcast_to(direction, positions.shape)
    radial_squared_gradient = 2.0 * (positions - axial[:, None] * direction)
    return (
        ScalarSample(axial, axial_gradient),
        ScalarSample(radial_squared, radial_squared_gradient),
    )


def rod_axial_gate(
    axial: np.ndarray, *, length: float | np.ndarray, taper_fraction: float
) -> np.ndarray:
    """Evaluate smooth one-sided rod support along its axial coordinate."""
    taper_width = np.asarray(length) * taper_fraction
    return smoothstep(axial / taper_width) * smoothstep(
        (np.asarray(length) - axial) / taper_width
    )


def rod_axial_gate_with_gradient(
    axial: ScalarSample,
    *,
    length: float | np.ndarray,
    length_gradient: np.ndarray,
    taper_fraction: float,
) -> ScalarSample:
    """Evaluate the axial support and its Cartesian gradient."""
    axial_values = axial.values
    length = np.broadcast_to(np.asarray(length), axial_values.shape)
    taper_width = length * taper_fraction
    start_input = axial_values / taper_width
    end_input = (length - axial_values) / taper_width
    start_gate = smoothstep(start_input)
    end_gate = smoothstep(end_input)
    start_gradient = smoothstep_derivative(start_input)[:, None] * (
        axial.gradients / taper_width[:, None]
        - axial_values[:, None]
        * length_gradient
        / (taper_width[:, None] * length[:, None])
    )
    end_gradient = smoothstep_derivative(end_input)[:, None] * (
        (length_gradient - axial.gradients) / taper_width[:, None]
        - (length - axial_values)[:, None]
        * length_gradient
        / (taper_width[:, None] * length[:, None])
    )
    return ScalarSample(
        start_gate * end_gate,
        start_gradient * end_gate[:, None] + end_gradient * start_gate[:, None],
    )


@register_jitable
def _rod_shape(
    x: float,
    y: float,
    z: float,
    squared_norm: float,
    direction: np.ndarray,
    width: float,
    length: float,
    taper_fraction: float,
    profile_power: float,
) -> tuple[float, float, float, float, float, float, float, float]:
    """Evaluate one rod's scalar geometry and tapered radial shape."""
    # Match the existing three-component einsum reduction order: X, Z, Y.
    axial = (x * direction[0] + z * direction[2]) + y * direction[1]
    radial_squared = max(squared_norm - axial * axial, 0.0)
    radial_base = max(1.0 - radial_squared / (width * width), 0.0)
    # NumPy squares the common quadratic profile directly rather than using pow.
    radial = (
        radial_base * radial_base
        if profile_power == 2.0
        else radial_base**profile_power
    )
    taper_width = length * taper_fraction
    start_input = axial / taper_width
    end_input = (length - axial) / taper_width
    start_gate = smoothstep_scalar(start_input)
    end_gate = smoothstep_scalar(end_input)
    return (
        axial,
        radial_squared,
        radial_base,
        radial,
        start_input,
        end_input,
        start_gate,
        end_gate,
    )


@register_jitable(inline="always")
def _rod_values(
    points: np.ndarray,
    directions: np.ndarray,
    widths: np.ndarray,
    lengths: np.ndarray,
    heights: np.ndarray,
    width_multiplier: np.ndarray,
    length_multiplier: np.ndarray,
    height_multiplier: np.ndarray,
    taper_fraction: float,
    profile_power: float,
) -> np.ndarray:
    """Accumulate rods in stored order, independently for each query."""
    values = np.empty(len(points), dtype=np.float64)
    for i in prange(len(points)):
        x, y, z = points[i, 0], points[i, 1], points[i, 2]
        squared_norm = (x * x + z * z) + y * y
        value = 0.0
        for rod in range(len(directions)):
            width = widths[rod] * width_multiplier[i]
            length = lengths[rod] * length_multiplier[i]
            height = heights[rod] * height_multiplier[i]
            _, _, _, radial, _, _, start_gate, end_gate = _rod_shape(
                x,
                y,
                z,
                squared_norm,
                directions[rod],
                width,
                length,
                taper_fraction,
                profile_power,
            )
            value += height * radial * (start_gate * end_gate)
        values[i] = value
    return values


@register_jitable(inline="always")
def _rod_values_with_gradient(
    points: np.ndarray,
    directions: np.ndarray,
    widths: np.ndarray,
    lengths: np.ndarray,
    heights: np.ndarray,
    width_multiplier: np.ndarray,
    length_multiplier: np.ndarray,
    height_multiplier: np.ndarray,
    width_multiplier_gradient: np.ndarray,
    length_multiplier_gradient: np.ndarray,
    height_multiplier_gradient: np.ndarray,
    taper_fraction: float,
    profile_power: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Accumulate relief and exact modifier-aware XYZ gradients without temporaries."""
    count = len(points)
    values = np.empty(count, dtype=np.float64)
    gradients = np.empty((count, 3), dtype=np.float64)
    for i in prange(count):
        x, y, z = points[i, 0], points[i, 1], points[i, 2]
        squared_norm = (x * x + z * z) + y * y
        value = 0.0
        for axis in range(3):
            gradients[i, axis] = 0.0
        for rod in range(len(directions)):
            width = widths[rod] * width_multiplier[i]
            length = lengths[rod] * length_multiplier[i]
            height = heights[rod] * height_multiplier[i]
            (
                axial,
                radial_squared,
                radial_base,
                radial,
                start_input,
                end_input,
                start_gate,
                end_gate,
            ) = _rod_shape(
                x,
                y,
                z,
                squared_norm,
                directions[rod],
                width,
                length,
                taper_fraction,
                profile_power,
            )
            axial_gate = start_gate * end_gate
            value += height * radial * axial_gate
            taper_width = length * taper_fraction
            start_derivative = smoothstep_derivative_scalar(start_input)
            end_derivative = smoothstep_derivative_scalar(end_input)
            radial_slope = 0.0
            if profile_power != 0.0:
                radial_slope = radial_base ** (profile_power - 1.0)
            for axis in range(3):
                direction = directions[rod, axis]
                width_gradient = widths[rod] * width_multiplier_gradient[i, axis]
                length_gradient = lengths[rod] * length_multiplier_gradient[i, axis]
                height_gradient = heights[rod] * height_multiplier_gradient[i, axis]
                radial_gradient = 0.0
                if profile_power != 0.0:
                    active = radial_base > 0.0
                    radial_gradient += (
                        -profile_power
                        * radial_slope
                        * (2.0 * (points[i, axis] - axial * direction))
                        / (width * width)
                    ) * active
                    radial_gradient += (
                        2.0
                        * profile_power
                        * radial_slope
                        * radial_squared
                        * width_gradient
                        / width**3
                    ) * active
                start_gradient = start_derivative * (
                    direction / taper_width
                    - axial * length_gradient / (taper_width * length)
                )
                end_gradient = end_derivative * (
                    (length_gradient - direction) / taper_width
                    - (length - axial) * length_gradient / (taper_width * length)
                )
                axial_gradient = start_gradient * end_gate + end_gradient * start_gate
                gradients[i, axis] += height_gradient * (
                    radial * axial_gate
                ) + height * (radial_gradient * axial_gate + radial * axial_gradient)
        values[i] = value
    return values, gradients


# Distinct cache identities, with one shared implementation per numerical path.
_rod_values_serial = njit(cache=True)(_rod_values)
_rod_gradients_serial = njit(cache=True)(_rod_values_with_gradient)


@njit(cache=True, parallel=True)
def _rod_values_parallel(
    points: np.ndarray,
    directions: np.ndarray,
    widths: np.ndarray,
    lengths: np.ndarray,
    heights: np.ndarray,
    width_multiplier: np.ndarray,
    length_multiplier: np.ndarray,
    height_multiplier: np.ndarray,
    taper_fraction: float,
    profile_power: float,
) -> np.ndarray:
    return _rod_values(
        points,
        directions,
        widths,
        lengths,
        heights,
        width_multiplier,
        length_multiplier,
        height_multiplier,
        taper_fraction,
        profile_power,
    )


@njit(cache=True, parallel=True)
def _rod_gradients_parallel(
    points: np.ndarray,
    directions: np.ndarray,
    widths: np.ndarray,
    lengths: np.ndarray,
    heights: np.ndarray,
    width_multiplier: np.ndarray,
    length_multiplier: np.ndarray,
    height_multiplier: np.ndarray,
    width_multiplier_gradient: np.ndarray,
    length_multiplier_gradient: np.ndarray,
    height_multiplier_gradient: np.ndarray,
    taper_fraction: float,
    profile_power: float,
) -> tuple[np.ndarray, np.ndarray]:
    return _rod_values_with_gradient(
        points,
        directions,
        widths,
        lengths,
        heights,
        width_multiplier,
        length_multiplier,
        height_multiplier,
        width_multiplier_gradient,
        length_multiplier_gradient,
        height_multiplier_gradient,
        taper_fraction,
        profile_power,
    )


# Measured query-by-rod work, keeping tiny batches below worker-launch cost.
_PARALLEL_ROD_WORK = 4096


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
    axial_gate = rod_axial_gate(axial, length=length, taper_fraction=taper_fraction)
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
        if count == 0 or len(self.directions) == 0:
            return ScalarSample(
                np.zeros(count, dtype=np.float64),
                np.zeros((count, 3), dtype=np.float64),
            )

        multipliers = []
        for value_sampler, gradient_sampler in (
            (self.sample_width_multiplier, self.sample_width_multiplier_gradient),
            (self.sample_length_multiplier, self.sample_length_multiplier_gradient),
            (self.sample_height_multiplier, self.sample_height_multiplier_gradient),
        ):
            if value_sampler is None:
                multipliers.append(
                    ScalarSample(
                        np.broadcast_to(1.0, (count,)),
                        np.broadcast_to(0.0, (count, 3)),
                    )
                )
            else:
                multipliers.append(gradient_sampler(query))
        width_multiplier, length_multiplier, height_multiplier = multipliers
        kernel = _rod_gradients_serial
        if count >= 64 and count * len(self.directions) >= _PARALLEL_ROD_WORK:
            kernel = _rod_gradients_parallel
        values, gradients = kernel(
            query,
            self.directions,
            self.widths,
            self.lengths,
            self.heights,
            width_multiplier.values,
            length_multiplier.values,
            height_multiplier.values,
            width_multiplier.gradients,
            length_multiplier.gradients,
            height_multiplier.gradients,
            self.taper_fraction,
            self.profile_power,
        )
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
        if count == 0 or len(self.directions) == 0:
            values = np.zeros(count, dtype=np.float64)
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
        kernel = _rod_values_serial
        if count >= 64 and count * len(self.directions) >= _PARALLEL_ROD_WORK:
            kernel = _rod_values_parallel
        values = kernel(
            query,
            self.directions,
            self.widths,
            self.lengths,
            self.heights,
            np.broadcast_to(width_multiplier, (count,)),
            np.broadcast_to(length_multiplier, (count,)),
            np.broadcast_to(height_multiplier, (count,)),
            self.taper_fraction,
            self.profile_power,
        )
        values.setflags(write=False)
        return values
