"""Continuous crust-seed preference used by tectonic polarity rules."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import VectorSample
from src.worldgen.field.region_influence import (
    RegionInfluenceField,
    RegionInfluenceSample,
)
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.utilities.curves import smoothstep


@dataclass(frozen=True, slots=True)
class PolarityConfig:
    """Relative scale and persistent tie bias for overriding-side preference."""

    preference_scale: float = 0.2
    seeded_bias: float = 0.25


@dataclass(frozen=True, slots=True)
class SubductionPreferenceField:
    """Derive the existing signed crust-seed preference vectors."""

    crust: CrustField
    regions: RegionInfluenceField

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample preference vectors at arbitrary Cartesian positions."""
        points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_regions(points, self.regions.sample(points))

    def sample_from_regions(
        self, positions: np.ndarray, sample: RegionInfluenceSample
    ) -> np.ndarray:
        """Reuse regional memberships to calculate the seed preference vector."""
        points = np.asarray(positions, dtype=np.float64)
        weights = sample.weights
        material_signs = np.where(self.crust.continental_regions, 1.0, -1.0)
        vectors = (weights * material_signs) @ self.crust.partition.seeds
        vectors -= points * (weights @ material_signs)[:, None]
        vectors.setflags(write=False)
        return vectors

    def sample_with_jacobian(
        self,
        positions: np.ndarray,
        sample: RegionInfluenceSample | None = None,
        gradients: np.ndarray | None = None,
    ) -> VectorSample:
        points = np.asarray(positions, dtype=np.float64)
        if sample is None or gradients is None:
            sample, gradients = self.regions.sample_with_gradient(points)
        signs = np.where(self.crust.continental_regions, 1.0, -1.0)
        signed_weights = sample.weights * signs
        values = signed_weights @ self.crust.partition.seeds
        values -= points * np.sum(signed_weights, axis=1)[:, None]
        jacobians = np.einsum(
            "nri,rj->nji",
            gradients * signs[None, :, None],
            self.crust.partition.seeds,
        )
        jacobians -= (
            np.eye(3)[None, :, :] * np.sum(signed_weights, axis=1)[:, None, None]
        )
        jacobians -= np.einsum(
            "ni,nj->nij",
            points,
            np.sum(gradients * signs[None, :, None], axis=1),
        )
        return VectorSample(values, jacobians)


def overriding_weights(
    preference: np.ndarray,
    seeded_sign: np.ndarray,
    *,
    directed: bool,
    config: PolarityConfig = PolarityConfig(),
) -> np.ndarray:
    """Return smooth weights for the ordered pair's second-side override."""
    if directed:
        scores = preference / config.preference_scale + config.seeded_bias * seeded_sign
    else:
        scores = config.seeded_bias * seeded_sign
    parameter = (scores + 1.0) * 0.5
    weights = smoothstep(parameter)
    weights.setflags(write=False)
    return weights


def overriding_weight_derivative(
    preference: np.ndarray,
    seeded_sign: np.ndarray,
    *,
    directed: bool,
    config: PolarityConfig = PolarityConfig(),
) -> np.ndarray:
    """Return derivative of overriding weight by preference vector dot."""
    if not directed:
        result = np.zeros_like(preference, dtype=np.float64)
    else:
        scores = preference / config.preference_scale + config.seeded_bias * seeded_sign
        parameter = np.clip((scores + 1.0) * 0.5, 0.0, 1.0)
        result = 3.0 * parameter * (1.0 - parameter) / config.preference_scale
    result.setflags(write=False)
    return result
