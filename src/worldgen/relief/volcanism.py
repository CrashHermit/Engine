"""Continuous volcanic suitability and relief fields in world-space XYZ."""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import (
    NoiseConfig,
    normalized_noise,
    normalized_noise_with_gradient,
)
from src.worldgen.field.rod import RodScalarField
from src.worldgen.field.seeds import generate_direction_seeds, select_weighted_seeds
from src.worldgen.field.warp import ShearWarpField
from src.worldgen.geology.model import SourceReliefGradientInputs, SourceReliefInputs
from src.worldgen.utilities.curves import (
    smooth_upper_bound,
    smooth_upper_bound_derivative,
)
from src.worldgen.relief.subduction import (
    subduction_profile,
    subduction_profile_with_partials,
)


@dataclass(frozen=True, slots=True)
class VolcanismConfig:
    """Controls hotspot and tectonic volcanic source placement and relief."""

    intraplate_strength: float = 1.0
    divergence_strength: float = 0.5
    saturation_half_width: float = 0.05
    relief_height_percent: float = 0.0047
    arc_width_percent: float = 12.0
    candidate_count: int = 4096
    hotspot_count: int = 48
    tectonic_count: int = 48
    hotspot_bias: float = 2.0
    tectonic_bias: float = 2.0
    hotspot_width_min_percent: float = 1.0
    hotspot_width_max_percent: float = 2.0
    hotspot_length_percent: float = 180.0
    hotspot_amplitude_min: float = 0.6
    hotspot_amplitude_max: float = 1.0
    tectonic_width_min_percent: float = 1.0
    tectonic_width_max_percent: float = 2.0
    tectonic_length_percent: float = 180.0
    tectonic_amplitude_min: float = 0.6
    tectonic_amplitude_max: float = 1.0
    rod_taper_fraction: float = 0.1
    rod_profile_power: float = 2.0
    suitability_frequency: float = 8.0


@dataclass(frozen=True, slots=True)
class VolcanicGradientSample:
    """Gradient samples for volcanic strength and relief."""

    strength: ScalarSample
    relief: ScalarSample


@dataclass(frozen=True, slots=True)
class VolcanicSample:
    """Per-query bounded volcanic strength and radius fraction relief."""

    strength: np.ndarray
    relief: np.ndarray


def _build_rods(
    directions: np.ndarray,
    rng: np.random.Generator,
    config: VolcanismConfig,
    *,
    hotspot: bool,
) -> RodScalarField:
    count = len(directions)
    if hotspot:
        low, high = config.hotspot_width_min_percent, config.hotspot_width_max_percent
        length, amp_low, amp_high = (
            config.hotspot_length_percent,
            config.hotspot_amplitude_min,
            config.hotspot_amplitude_max,
        )
    else:
        low, high = config.tectonic_width_min_percent, config.tectonic_width_max_percent
        length, amp_low, amp_high = (
            config.tectonic_length_percent,
            config.tectonic_amplitude_min,
            config.tectonic_amplitude_max,
        )
    return RodScalarField(
        directions=directions,
        widths=rng.uniform(low / 100.0, high / 100.0, size=count),
        lengths=np.full(count, length / 100.0, dtype=np.float64),
        heights=rng.uniform(amp_low, amp_high, size=count),
        taper_fraction=config.rod_taper_fraction,
        profile_power=config.rod_profile_power,
    )


@dataclass(frozen=True, slots=True)
class VolcanicField:
    """Suitability-weighted rods placed once, then sampled in world coordinates."""

    sample_relief_inputs: Callable[[np.ndarray], SourceReliefInputs]
    noise_seed: int
    warp: ShearWarpField
    config: VolcanismConfig = VolcanismConfig()
    sample_relief_inputs_with_gradient: Callable[
        [np.ndarray], SourceReliefGradientInputs
    ] = field(kw_only=True)
    hotspots: RodScalarField = field(init=False, repr=False)
    tectonic_rods: RodScalarField = field(init=False, repr=False)

    def __post_init__(self) -> None:
        config = self.config
        root = self.noise_seed & 0xFFFFFFFF
        candidate_rng = np.random.default_rng(
            np.random.SeedSequence([root, 0x43414E44])
        )
        candidates = generate_direction_seeds(config.candidate_count, rng=candidate_rng)
        candidates = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)
        hotspot_rng = np.random.default_rng(np.random.SeedSequence([root, 0x484F5453]))
        tectonic_rng = np.random.default_rng(np.random.SeedSequence([root, 0x54454348]))
        hotspot_directions = (
            select_weighted_seeds(
                candidates,
                self.hotspot_suitability(candidates) ** config.hotspot_bias,
                config.hotspot_count,
                rng=hotspot_rng,
            )
            if config.hotspot_count
            else candidates[:0]
        )
        tectonic_directions = (
            select_weighted_seeds(
                candidates,
                self.tectonic_suitability(candidates) ** config.tectonic_bias,
                config.tectonic_count,
                rng=tectonic_rng,
            )
            if config.tectonic_count
            else candidates[:0]
        )
        object.__setattr__(
            self,
            "hotspots",
            _build_rods(hotspot_directions, hotspot_rng, config, hotspot=True),
        )
        object.__setattr__(
            self,
            "tectonic_rods",
            _build_rods(tectonic_directions, tectonic_rng, config, hotspot=False),
        )

    def hotspot_suitability(self, world_positions: np.ndarray) -> np.ndarray:
        values = normalized_noise(
            np.asarray(world_positions, dtype=np.float64),
            NoiseConfig(octaves=3, base_frequency=self.config.suitability_frequency),
            seed=self.noise_seed ^ 0x13579B,
        )
        values.setflags(write=False)
        return values

    def hotspot_suitability_with_gradient(
        self, world_positions: np.ndarray
    ) -> ScalarSample:
        return normalized_noise_with_gradient(
            np.asarray(world_positions, dtype=np.float64),
            NoiseConfig(octaves=3, base_frequency=self.config.suitability_frequency),
            seed=self.noise_seed ^ 0x13579B,
        )

    def _tectonic_suitability(self, inputs: SourceReliefInputs) -> np.ndarray:
        context = inputs.context
        pair_values = np.zeros(len(inputs.query_indices), dtype=np.float64)
        width = self.config.arc_width_percent / 100.0
        for i, distance in enumerate(context.plane_distance):
            b_arc = subduction_profile(distance, width) - subduction_profile(
                distance, width, arc_height_multiplier=0.0
            )
            a_arc = subduction_profile(-distance, width) - subduction_profile(
                -distance, width, arc_height_multiplier=0.0
            )
            arc = (
                context.b_overrides_weight[i] * b_arc
                + (1.0 - context.b_overrides_weight[i]) * a_arc
            )
            land_influence = (1.0 - context.continental_blend[i]) * context.influence[i]
            pair_values[i] = (
                arc * context.convergence[i] * land_influence
                + self.config.divergence_strength
                * context.divergence[i]
                * land_influence
            )
        values = np.zeros(len(inputs.continental_weight), dtype=np.float64)
        np.add.at(values, inputs.query_indices, pair_values)
        return values

    def tectonic_suitability(self, world_positions: np.ndarray) -> np.ndarray:
        inputs = self.sample_relief_inputs(
            self.warp.sample(np.asarray(world_positions, dtype=np.float64))
        )
        values = self._tectonic_suitability(inputs)
        values.setflags(write=False)
        return values

    def tectonic_suitability_with_gradient(
        self, world_positions: np.ndarray
    ) -> ScalarSample:
        positions = np.asarray(world_positions, dtype=np.float64)
        transformed = self.warp.sample_with_jacobian(positions)
        inputs = self.sample_relief_inputs_with_gradient(transformed.values)
        pair, pair_grad = inputs.context.sample, inputs.context
        pair_values = np.zeros(len(pair.plane_distance), dtype=np.float64)
        pair_gradients = np.zeros((len(pair.plane_distance), 3), dtype=np.float64)
        width = self.config.arc_width_percent / 100.0
        for i, distance in enumerate(pair.plane_distance):
            b, bd, _, _ = subduction_profile_with_partials(distance, width)
            bt, btd, _, _ = subduction_profile_with_partials(
                distance, width, arc_height_multiplier=0.0
            )
            a, ad, _, _ = subduction_profile_with_partials(-distance, width)
            at, atd, _, _ = subduction_profile_with_partials(
                -distance, width, arc_height_multiplier=0.0
            )
            pb, pa = b - bt, a - at
            dpb = (bd - btd) * pair_grad.plane_distance_gradients[i]
            dpa = -(ad - atd) * pair_grad.plane_distance_gradients[i]
            wb = pair.b_overrides_weight[i]
            arc = wb * pb + (1.0 - wb) * pa
            arc_grad = (
                pair_grad.b_overrides_weight_gradients[i] * (pb - pa)
                + wb * dpb
                + (1.0 - wb) * dpa
            )
            conv, land, influence = (
                pair.convergence[i],
                1.0 - pair.continental_blend[i],
                pair.influence[i],
            )
            div = pair.divergence[i]
            pair_values[i] = (
                arc * conv * land * influence
                + self.config.divergence_strength * div * land * influence
            )
            pair_gradients[i] = (
                arc_grad * conv * land * influence
                + arc
                * (
                    pair_grad.convergence_gradients[i] * land * influence
                    - conv * pair_grad.continental_blend_gradients[i] * influence
                    + conv * land * pair_grad.influence_gradients[i]
                )
                + self.config.divergence_strength
                * (
                    pair_grad.divergence_gradients[i] * land * influence
                    - div * pair_grad.continental_blend_gradients[i] * influence
                    + div * land * pair_grad.influence_gradients[i]
                )
            )
        values = np.zeros(len(positions), dtype=np.float64)
        gradients = np.zeros((len(positions), 3), dtype=np.float64)
        np.add.at(values, inputs.query_indices, pair_values)
        np.add.at(gradients, inputs.query_indices, pair_gradients)
        gradients = np.einsum("ni,nij->nj", gradients, transformed.jacobians)
        return ScalarSample(values, gradients)

    def sample_intraplate(self, positions: np.ndarray) -> np.ndarray:
        values = smooth_upper_bound(
            self.config.intraplate_strength * self.hotspots.sample(positions),
            upper=1.0,
            transition_half_width=self.config.saturation_half_width,
        )
        values.setflags(write=False)
        return values

    def sample_with_gradient(self, positions: np.ndarray) -> VolcanicGradientSample:
        query = np.asarray(positions, dtype=np.float64)
        hotspot = self.hotspots.sample_with_gradient(query)
        tectonic = self.tectonic_rods.sample_with_gradient(query)
        raw = self.config.intraplate_strength * hotspot.values + tectonic.values
        raw_gradient = (
            self.config.intraplate_strength * hotspot.gradients + tectonic.gradients
        )
        strength = smooth_upper_bound(
            raw, upper=1.0, transition_half_width=self.config.saturation_half_width
        )
        derivative = smooth_upper_bound_derivative(
            raw, upper=1.0, transition_half_width=self.config.saturation_half_width
        )
        factor = self.config.relief_height_percent / 100.0
        return VolcanicGradientSample(
            ScalarSample(strength, derivative[:, None] * raw_gradient),
            ScalarSample(
                factor * strength, factor * derivative[:, None] * raw_gradient
            ),
        )

    def sample(self, positions: np.ndarray) -> VolcanicSample:
        query = np.asarray(positions, dtype=np.float64)
        raw = self.config.intraplate_strength * self.hotspots.sample(
            query
        ) + self.tectonic_rods.sample(query)
        strength = smooth_upper_bound(
            raw, upper=1.0, transition_half_width=self.config.saturation_half_width
        )
        relief = strength * (self.config.relief_height_percent / 100.0)
        for values in (strength, relief):
            values.setflags(write=False)
        return VolcanicSample(strength, relief)
