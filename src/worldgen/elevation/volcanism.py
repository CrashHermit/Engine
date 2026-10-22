"""Continuous volcanic potential and relief fields in source-space XYZ."""

from dataclasses import dataclass, field

import numpy as np

from src.worldgen.elevation.profiles import (
    subduction_profile,
    subduction_profile_with_partials,
)
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import (
    NoiseConfig,
    noise_multiplier,
    noise_multiplier_with_gradient,
    normalized_noise,
    normalized_noise_with_gradient,
)
from src.worldgen.field.rod import RodScalarField
from src.worldgen.field.seeds import generate_direction_seeds
from src.worldgen.geology.field import GeologyField
from src.worldgen.geology.model import GeologySample, GeologyGradientSample
from src.worldgen.utilities.curves import smoothstep, smooth_upper_bound


@dataclass(frozen=True, slots=True)
class VolcanismConfig:
    """Settings for continuous volcanic arc and intraplate relief."""

    arc_strength: float = 0.5
    # Intraplate strength now scales sparse hotspot rods, not broad noise provinces.
    intraplate_strength: float = 1.0
    # Dimensionless knee around strength one; weak contributions stay unchanged.
    saturation_half_width: float = 0.05
    relief_height_percent: float = 0.0047
    threshold: float = 0.65
    transition_width: float = 0.12
    concentration_frequency: float = 14.0
    arc_width_percent: float = 12.0
    hotspot_count: int = 48
    hotspot_width_min_percent: float = 1.0
    hotspot_width_max_percent: float = 2.0
    hotspot_length_percent: float = 180.0
    hotspot_amplitude_min: float = 0.6
    hotspot_amplitude_max: float = 1.0
    hotspot_taper_fraction: float = 0.1
    hotspot_profile_power: float = 2.0
    hotspot_width_noise_strength: float = 0.05
    hotspot_height_noise_strength: float = 0.1
    hotspot_noise_frequency: float = 8.0


def _height_multiplier_with_gradient(
    positions: np.ndarray, *, seed: int, config: NoiseConfig, strength: float
) -> ScalarSample:
    noise = normalized_noise_with_gradient(positions, config, seed=seed)
    return ScalarSample(
        1.0 - strength + strength * noise.values,
        strength * noise.gradients,
    )


def build_hotspot_rods(noise_seed: int, config: VolcanismConfig) -> RodScalarField:
    """Build deterministic, independently seeded origin-based hotspot rods."""
    rng = np.random.default_rng(
        np.random.SeedSequence([noise_seed & 0xFFFFFFFF, 0x524F44])
    )
    directions = generate_direction_seeds(config.hotspot_count, rng=rng)
    widths = rng.uniform(
        config.hotspot_width_min_percent / 100.0,
        config.hotspot_width_max_percent / 100.0,
        size=config.hotspot_count,
    )
    heights = rng.uniform(
        config.hotspot_amplitude_min,
        config.hotspot_amplitude_max,
        size=config.hotspot_count,
    )
    lengths = np.full(
        config.hotspot_count, config.hotspot_length_percent / 100.0, dtype=np.float64
    )
    width_sampler = None
    width_gradient_sampler = None
    if config.hotspot_width_noise_strength != 0:
        width_sampler = lambda positions: noise_multiplier(
            positions,
            seed=noise_seed + 2,
            frequency=config.hotspot_noise_frequency,
            strength=config.hotspot_width_noise_strength,
        )
        width_gradient_sampler = lambda positions: noise_multiplier_with_gradient(
            positions,
            seed=noise_seed + 2,
            frequency=config.hotspot_noise_frequency,
            strength=config.hotspot_width_noise_strength,
        )
    height_sampler = None
    height_gradient_sampler = None
    if config.hotspot_height_noise_strength != 0:
        height_noise_config = NoiseConfig(
            octaves=2, base_frequency=config.hotspot_noise_frequency
        )
        height_sampler = lambda positions: (
            1.0
            - config.hotspot_height_noise_strength
            + config.hotspot_height_noise_strength
            * normalized_noise(positions, height_noise_config, seed=noise_seed + 3)
        )
        height_gradient_sampler = lambda positions: _height_multiplier_with_gradient(
            positions,
            seed=noise_seed + 3,
            config=height_noise_config,
            strength=config.hotspot_height_noise_strength,
        )
    return RodScalarField(
        directions=directions,
        widths=widths,
        lengths=lengths,
        heights=heights,
        taper_fraction=config.hotspot_taper_fraction,
        profile_power=config.hotspot_profile_power,
        sample_width_multiplier=width_sampler,
        sample_height_multiplier=height_sampler,
        sample_width_multiplier_gradient=width_gradient_sampler,
        sample_height_multiplier_gradient=height_gradient_sampler,
    )


@dataclass(frozen=True, slots=True)
class VolcanicGradientSample:
    """Gradient samples for bounded potential, strength, and volcanic relief."""

    potential: ScalarSample
    strength: ScalarSample
    relief: ScalarSample


def _smooth_upper_bound_derivative(
    values: np.ndarray, *, upper: float, transition_half_width: float
) -> np.ndarray:
    lower = upper - transition_half_width
    position = np.clip((values - lower) / (2.0 * transition_half_width), 0.0, 1.0)
    return np.where(
        values <= lower,
        1.0,
        np.where(values >= upper + transition_half_width, 0.0, 1.0 - position),
    )


def _smoothstep_derivative(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, 0.0, 1.0)
    return np.where(
        (values > 0.0) & (values < 1.0), 6.0 * clipped * (1.0 - clipped), 0.0
    )


@dataclass(frozen=True, slots=True)
class VolcanicSample:
    """Per-query bounded volcanic potential, strength, and radius fraction relief."""

    potential: np.ndarray
    strength: np.ndarray
    relief: np.ndarray


@dataclass(frozen=True, slots=True)
class VolcanicField:
    """Compose tectonic volcanic arcs with independently seeded hotspot rods."""

    geology: GeologyField
    noise_seed: int
    config: VolcanismConfig = VolcanismConfig()
    hotspots: RodScalarField = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "hotspots", build_hotspot_rods(self.noise_seed, self.config)
        )

    def sample_intraplate(self, positions: np.ndarray) -> np.ndarray:
        """Sample bounded hotspot strength independently of arc concentration."""
        values = smooth_upper_bound(
            self.config.intraplate_strength * self.hotspots.sample(positions),
            upper=1.0,
            transition_half_width=self.config.saturation_half_width,
        )
        values.setflags(write=False)
        return values

    def sample_with_gradient(
        self,
        positions: np.ndarray,
        *,
        geology_sample: GeologyGradientSample | None = None,
    ) -> VolcanicGradientSample:
        """Sample volcanic potential, strength, and relief gradients in XYZ."""
        query = np.asarray(positions, dtype=np.float64)
        count = len(query)
        if count == 0:
            empty = np.empty(0, dtype=np.float64)
            zero = np.empty((0, 3), dtype=np.float64)
            sample = ScalarSample(empty, zero)
            return VolcanicGradientSample(sample, sample, sample)
        geo = (
            self.geology.sample_source_with_gradient(query)
            if geology_sample is None
            else geology_sample
        )
        output = self.sample(query, geology_sample=geo.sample)
        context = geo.context.sample
        context_gradient = geo.context
        arc = np.zeros(count, dtype=np.float64)
        arc_gradient = np.zeros((count, 3), dtype=np.float64)
        width = self.config.arc_width_percent / 100.0
        pair_ids = geo.sample.motion.query_indices
        if len(context.plane_distance):
            pair_arc = np.zeros(len(context.plane_distance), dtype=np.float64)
            pair_arc_gradient = np.zeros((len(pair_arc), 3), dtype=np.float64)
            for index in range(len(pair_arc)):
                distance = context.plane_distance[index]
                toward_b, toward_b_d, _, _ = subduction_profile_with_partials(
                    distance, width
                )
                trench_b, trench_b_d, _, _ = subduction_profile_with_partials(
                    distance, width, arc_height_multiplier=0.0
                )
                toward_a, toward_a_d, _, _ = subduction_profile_with_partials(
                    -distance, width
                )
                trench_a, trench_a_d, _, _ = subduction_profile_with_partials(
                    -distance, width, arc_height_multiplier=0.0
                )
                profile_b = toward_b - trench_b
                profile_a = toward_a - trench_a
                profile_b_gradient = (
                    toward_b_d - trench_b_d
                ) * context_gradient.plane_distance_gradients[index]
                profile_a_gradient = (
                    -(toward_a_d - trench_a_d)
                    * context_gradient.plane_distance_gradients[index]
                )
                b_weight = context.b_overrides_weight[index]
                response = b_weight * profile_b + (1.0 - b_weight) * profile_a
                response_gradient = (
                    context_gradient.b_overrides_weight_gradients[index]
                    * (profile_b - profile_a)
                    + b_weight * profile_b_gradient
                    + (1.0 - b_weight) * profile_a_gradient
                )
                convergence = context.convergence[index]
                land = 1.0 - context.continental_blend[index]
                influence = context.influence[index]
                pair_arc[index] = response * convergence * land * influence
                pair_arc_gradient[index] = (
                    response_gradient * convergence * land * influence
                    + response
                    * (
                        context_gradient.convergence_gradients[index] * land * influence
                        - convergence
                        * context_gradient.continental_blend_gradients[index]
                        * influence
                        + convergence
                        * land
                        * context_gradient.influence_gradients[index]
                    )
                )
            np.add.at(arc, pair_ids, pair_arc)
            np.add.at(arc_gradient, pair_ids, pair_arc_gradient)

        concentration = normalized_noise_with_gradient(
            query,
            NoiseConfig(octaves=2, base_frequency=self.config.concentration_frequency),
            seed=self.noise_seed + 1,
        )
        gate_input = (
            concentration.values - self.config.threshold
        ) / self.config.transition_width + 0.5
        gate = smoothstep(gate_input)
        gate_gradient = (
            _smoothstep_derivative(gate_input)[:, None]
            * concentration.gradients
            / self.config.transition_width
        )
        hotspot = self.hotspots.sample_with_gradient(query)
        raw_arc = self.config.arc_strength * arc
        raw_arc_gradient = self.config.arc_strength * arc_gradient
        raw_hotspot = self.config.intraplate_strength * hotspot.values
        raw_hotspot_gradient = self.config.intraplate_strength * hotspot.gradients
        potential_input = raw_arc + raw_hotspot
        strength_input = raw_arc * gate**2 + raw_hotspot
        potential_gradient = _smooth_upper_bound_derivative(
            potential_input,
            upper=1.0,
            transition_half_width=self.config.saturation_half_width,
        )[:, None] * (raw_arc_gradient + raw_hotspot_gradient)
        strength_gradient = _smooth_upper_bound_derivative(
            strength_input,
            upper=1.0,
            transition_half_width=self.config.saturation_half_width,
        )[:, None] * (
            raw_arc_gradient * gate[:, None] ** 2
            + 2.0 * raw_arc[:, None] * gate[:, None] * gate_gradient
            + raw_hotspot_gradient
        )
        factor = self.config.relief_height_percent / 100.0
        return VolcanicGradientSample(
            ScalarSample(output.potential, potential_gradient),
            ScalarSample(output.strength, strength_gradient),
            ScalarSample(output.relief, factor * strength_gradient),
        )

    def sample(
        self,
        positions: np.ndarray,
        *,
        geology_sample: GeologySample | None = None,
    ) -> VolcanicSample:
        """Sample volcanic fields at paired XYZ coordinates without projection."""
        query = np.asarray(positions, dtype=np.float64)
        count = len(query)
        if count == 0:
            empty = np.empty(0, dtype=np.float64)
            empty.setflags(write=False)
            return VolcanicSample(empty, empty, empty)

        sample = (
            self.geology.sample_source(query)
            if geology_sample is None
            else geology_sample
        )
        context = sample.context
        pair_count = len(context.plane_distance)
        arc = np.zeros(count, dtype=np.float64)
        if pair_count:
            # The existing subduction profile has trench plus an overriding-side
            # arc; use only its positive arc component so volcanic relief does not
            # duplicate the trench response. Blend the two ordered orientations.

            convergence = context.convergence
            pair_arc = np.zeros(pair_count, dtype=np.float64)
            for i in range(pair_count):
                distance = context.plane_distance[i]
                toward_b = subduction_profile(
                    distance, self.config.arc_width_percent / 100.0
                ) - subduction_profile(
                    distance,
                    self.config.arc_width_percent / 100.0,
                    arc_height_multiplier=0.0,
                )
                toward_a = subduction_profile(
                    -distance, self.config.arc_width_percent / 100.0
                ) - subduction_profile(
                    -distance,
                    self.config.arc_width_percent / 100.0,
                    arc_height_multiplier=0.0,
                )
                response = (
                    context.b_overrides_weight[i] * toward_b
                    + (1.0 - context.b_overrides_weight[i]) * toward_a
                )
                pair_arc[i] = (
                    response
                    * convergence[i]
                    * (1.0 - context.continental_blend[i])
                    * context.influence[i]
                )
            np.add.at(arc, sample.motion.query_indices, pair_arc)

        concentration = normalized_noise(
            query,
            NoiseConfig(octaves=2, base_frequency=self.config.concentration_frequency),
            seed=self.noise_seed + 1,
        )
        gate = smoothstep(
            (concentration - self.config.threshold) / self.config.transition_width + 0.5
        )
        raw_arc = self.config.arc_strength * arc
        raw_hotspot = self.config.intraplate_strength * self.hotspots.sample(query)
        potential = smooth_upper_bound(
            raw_arc + raw_hotspot,
            upper=1.0,
            transition_half_width=self.config.saturation_half_width,
        )
        strength = smooth_upper_bound(
            raw_arc * gate**2 + raw_hotspot,
            upper=1.0,
            transition_half_width=self.config.saturation_half_width,
        )
        relief = strength * (self.config.relief_height_percent / 100.0)
        for values in (potential, strength, relief):
            values.setflags(write=False)
        return VolcanicSample(potential, strength, relief)
