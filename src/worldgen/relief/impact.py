"""Deterministic additive volumetric meteor crater relief."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.rod import (
    rod_axial_gate,
    rod_axial_gate_with_gradient,
    rod_coordinates,
    rod_coordinates_with_gradient,
)
from src.worldgen.field.seeds import generate_direction_seeds


@dataclass(frozen=True, slots=True)
class ImpactConfig:
    """Impact sizes and counts as percentages of the unit world radius."""

    count: int = 16
    radius_min_percent: float = 0.8
    radius_max_percent: float = 3.0
    depth_min_percent: float = 0.003
    depth_max_percent: float = 0.02
    rim_height_min_percent: float = 0.0005
    rim_height_max_percent: float = 0.004
    rim_width_fraction: float = 0.25
    length_percent: float = 180.0
    taper_fraction: float = 0.1


def impact_profile(
    radial_squared: np.ndarray,
    *,
    radius: float | np.ndarray,
    depth: float | np.ndarray,
    rim_height: float | np.ndarray,
    rim_width_fraction: float,
) -> np.ndarray:
    """Evaluate the C2 bowl and raised annular-rim profile."""
    u = np.asarray(radial_squared) / np.asarray(radius) ** 2
    b = (1.0 - rim_width_fraction) ** 2
    bowl = -np.asarray(depth) * np.maximum(1.0 - u / b, 0.0) ** 3
    t = (u - b) / (1.0 - b)
    tc = np.clip(t, 0.0, 1.0)
    bump = 64.0 * tc**3 * (1.0 - tc) ** 3
    rim = np.asarray(rim_height) * np.where((t > 0.0) & (t < 1.0), bump, 0.0)
    return bowl + rim


def impact_profile_with_partials(
    radial_squared: np.ndarray,
    *,
    radius: float | np.ndarray,
    depth: float | np.ndarray,
    rim_height: float | np.ndarray,
    rim_width_fraction: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return profile and analytic partials for squared radius, radius, depth, and rim height."""
    q = np.asarray(radial_squared)
    r = np.asarray(radius)
    d = np.asarray(depth)
    h = np.asarray(rim_height)
    u = q / r**2
    b = (1.0 - rim_width_fraction) ** 2
    x = 1.0 - u / b
    bowl_base = np.maximum(x, 0.0)
    bowl = -d * bowl_base**3
    db_du = np.where(x > 0.0, 3.0 * d * bowl_base**2 / b, 0.0)
    t = (u - b) / (1.0 - b)
    active = (t > 0.0) & (t < 1.0)
    tc = np.clip(t, 0.0, 1.0)
    bump = 64.0 * tc**3 * (1.0 - tc) ** 3
    bump_derivative = 192.0 * tc**2 * (1.0 - tc) ** 2 * (1.0 - 2.0 * tc)
    bump_derivative = np.where(active, bump_derivative, 0.0)
    value = bowl + h * np.where(active, bump, 0.0)
    dv_du = db_du + h * bump_derivative / (1.0 - b)
    du_dq = 1.0 / r**2
    du_dr = -2.0 * u / r
    return (
        value,
        dv_du * du_dq,
        dv_du * du_dr,
        -(bowl_base**3),
        np.where(active, bump, 0.0),
    )


@dataclass(frozen=True, slots=True)
class ImpactField:
    """Immutable collection of seeded, one-sided finite impact rods."""

    directions: np.ndarray
    radii: np.ndarray
    depths: np.ndarray
    rim_heights: np.ndarray
    lengths: np.ndarray
    config: ImpactConfig = ImpactConfig()

    def __post_init__(self) -> None:
        directions = np.array(self.directions, dtype=np.float64, copy=True)
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        directions.setflags(write=False)
        object.__setattr__(self, "directions", directions)
        for name in ("radii", "depths", "rim_heights", "lengths"):
            values = np.array(getattr(self, name), dtype=np.float64, copy=True)
            values.setflags(write=False)
            object.__setattr__(self, name, values)

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        points = np.asarray(positions, dtype=np.float64)
        values = np.zeros(len(points), dtype=np.float64)
        gradients = np.zeros_like(points)
        length_gradient = np.zeros_like(points)
        for direction, radius, depth, rim_height, length in zip(
            self.directions,
            self.radii,
            self.depths,
            self.rim_heights,
            self.lengths,
            strict=True,
        ):
            axial_sample, radial_sample = rod_coordinates_with_gradient(
                points, direction
            )
            axial_gate = rod_axial_gate_with_gradient(
                axial_sample,
                length=length,
                length_gradient=length_gradient,
                taper_fraction=self.config.taper_fraction,
            )
            profile, partial_q, _, _, _ = impact_profile_with_partials(
                radial_sample.values,
                radius=radius,
                depth=depth,
                rim_height=rim_height,
                rim_width_fraction=self.config.rim_width_fraction,
            )
            values += profile * axial_gate.values
            gradients += (partial_q * axial_gate.values)[
                :, None
            ] * radial_sample.gradients + profile[:, None] * axial_gate.gradients
        return ScalarSample(values, gradients)

    def sample(self, positions: np.ndarray) -> np.ndarray:
        points = np.asarray(positions, dtype=np.float64)
        values = np.zeros(len(points), dtype=np.float64)
        for direction, radius, depth, rim_height, length in zip(
            self.directions,
            self.radii,
            self.depths,
            self.rim_heights,
            self.lengths,
            strict=True,
        ):
            axial, radial_squared = rod_coordinates(points, direction)
            gate = rod_axial_gate(
                axial, length=length, taper_fraction=self.config.taper_fraction
            )
            values += (
                impact_profile(
                    radial_squared,
                    radius=radius,
                    depth=depth,
                    rim_height=rim_height,
                    rim_width_fraction=self.config.rim_width_fraction,
                )
                * gate
            )
        values.setflags(write=False)
        return values


def generate_impact_field(
    config: ImpactConfig = ImpactConfig(), *, seed: int
) -> ImpactField:
    """Generate immutable impact geometry from an isolated deterministic stream."""
    rng = np.random.default_rng(np.random.SeedSequence([seed & 0xFFFFFFFF, 0x494D50]))
    directions = generate_direction_seeds(config.count, rng=rng)
    radii = rng.uniform(
        config.radius_min_percent / 100.0,
        config.radius_max_percent / 100.0,
        size=config.count,
    )
    depths = rng.uniform(
        config.depth_min_percent / 100.0,
        config.depth_max_percent / 100.0,
        size=config.count,
    )
    rims = rng.uniform(
        config.rim_height_min_percent / 100.0,
        config.rim_height_max_percent / 100.0,
        size=config.count,
    )
    lengths = np.full(config.count, config.length_percent / 100.0, dtype=np.float64)
    return ImpactField(directions, radii, depths, rims, lengths, config)
