"""Continuous crust-material influence sampled from regional memberships."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceField,
    RegionInfluenceSample,
)
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.utilities.curves import smoothstep, smoothstep_derivative


@dataclass(frozen=True, slots=True)
class MaterialBlendConfig:
    """Continental influence interval that blends geological profile families."""

    midpoint: float = 0.5
    transition_width: float = 0.2


@dataclass(frozen=True, slots=True)
class CrustInfluenceSample:
    """Smooth continental membership and its complementary oceanic influence."""

    continental_weight: np.ndarray

    @property
    def oceanic_weight(self) -> np.ndarray:
        """Return the complementary read-only oceanic membership."""
        weight = 1.0 - self.continental_weight
        weight.setflags(write=False)
        return weight


@dataclass(frozen=True, slots=True)
class CrustInfluenceField:
    """Derive continuous material values from labeled regional membership."""

    crust: CrustField
    regions: RegionInfluenceField

    def sample(self, positions: np.ndarray) -> CrustInfluenceSample:
        """Sample material influence at arbitrary Cartesian positions."""
        query_points = np.asarray(positions, dtype=np.float64)
        return self.sample_from_regions(self.regions.sample(query_points))

    def sample_from_regions(
        self, sample: RegionInfluenceSample
    ) -> CrustInfluenceSample:
        """Reuse regional weights to derive scalar crust-material influence."""
        continental_weight = sample.weights @ self.crust.continental_regions.astype(
            np.float64
        )
        continental_weight.setflags(write=False)
        return CrustInfluenceSample(continental_weight)

    def sample_with_gradient(
        self, positions: np.ndarray
    ) -> tuple[CrustInfluenceSample, np.ndarray]:
        regions, gradients = self.regions.sample_with_gradient(positions)
        return self.sample_from_regions_with_gradient(regions, gradients)

    def sample_from_regions_with_gradient(
        self, regions: RegionInfluenceSample, gradients: np.ndarray
    ) -> tuple[CrustInfluenceSample, np.ndarray]:
        sample = self.sample_from_regions(regions)
        result = np.einsum(
            "nri,r->ni", gradients, self.crust.continental_regions.astype(np.float64)
        )
        result.setflags(write=False)
        return sample, result


def continental_response_weight(
    continental_weight: np.ndarray,
    config: MaterialBlendConfig = MaterialBlendConfig(),
) -> np.ndarray:
    """Map continental influence to a clamped, smooth response blend."""
    weight = smoothstep(
        (np.asarray(continental_weight, dtype=np.float64) - config.midpoint)
        / config.transition_width
        + 0.5
    )
    weight.setflags(write=False)
    return weight


def continental_response_derivative(
    continental_weight: np.ndarray,
    config: MaterialBlendConfig = MaterialBlendConfig(),
) -> np.ndarray:
    """Return the derivative of continental response by input weight."""
    parameter = (
        np.asarray(continental_weight, dtype=np.float64) - config.midpoint
    ) / config.transition_width + 0.5
    result = smoothstep_derivative(parameter) / config.transition_width
    result.setflags(write=False)
    return result
