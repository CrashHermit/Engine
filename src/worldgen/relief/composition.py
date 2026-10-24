"""World-space elevation composition and component sampling."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.relief.field import SourceReliefField
from src.worldgen.relief.impact import ImpactField
from src.worldgen.relief.model import ElevationResult
from src.worldgen.relief.variation import TerrainVariationField
from src.worldgen.relief.volcanism import VolcanicField
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.warp import ShearWarpField
from src.worldgen.geology.model import SourceReliefInputs


from src.worldgen.geometry.differential import pullback_covectors


def _compose_total(
    source: np.ndarray, volcanic: np.ndarray, impact: np.ndarray, variation: np.ndarray
) -> np.ndarray:
    total = source + volcanic
    total = total + impact
    total = total + variation
    total.setflags(write=False)
    return total


@dataclass(frozen=True, slots=True)
class ElevationField:
    """Own source and world-space elevation components and their sum."""

    source_relief: SourceReliefField
    warp: ShearWarpField
    volcanism: VolcanicField
    impact_relief: ImpactField
    variation: TerrainVariationField

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample total radius-fraction elevation."""
        query = np.asarray(positions, dtype=np.float64)
        source_positions = self.warp.sample(query)
        source = self.source_relief.sample_total_source(source_positions)
        volcanic = self.volcanism.sample(query).relief
        impact = self.impact_relief.sample(query)
        variation = self.variation.sample_fraction(query)
        return _compose_total(source, volcanic, impact, variation)

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Sample total elevation and its analytic XYZ gradient."""
        query = np.asarray(positions, dtype=np.float64)
        transformed = self.warp.sample_with_jacobian(query)
        source = self.source_relief.sample_total_source_with_gradient(
            transformed.values
        )
        volcanic = self.volcanism.sample_with_gradient(query).relief
        impact = self.impact_relief.sample_with_gradient(query)
        variation = self.variation.sample_fraction_with_gradient(query)
        values = _compose_total(
            source.values, volcanic.values, impact.values, variation.values
        )
        gradients = pullback_covectors(source.gradients, transformed.jacobians)
        gradients = gradients + volcanic.gradients
        gradients = gradients + impact.gradients
        gradients = gradients + variation.gradients
        values.setflags(write=False)
        gradients.setflags(write=False)
        return ScalarSample(values, gradients)

    def sample_components(
        self,
        positions: np.ndarray,
        *,
        source_positions: np.ndarray | None = None,
        relief_inputs: SourceReliefInputs | None = None,
    ) -> ElevationResult:
        """Sample named elevation components, reusing supplied source dependencies."""
        query = np.asarray(positions, dtype=np.float64)
        source_query = (
            self.warp.sample(query) if source_positions is None else source_positions
        )
        source = self.source_relief.sample_source(
            source_query, relief_inputs=relief_inputs
        )
        volcanic = self.volcanism.sample(query)
        impact = self.impact_relief.sample(query)
        variation = self.variation.sample_fraction(query)
        total = _compose_total(source.total, volcanic.relief, impact, variation)
        return ElevationResult(
            coastal_elevation=source.coastal_elevation,
            volcanic_strength=volcanic.strength,
            volcanic_relief=volcanic.relief,
            convergent_relief=source.convergent_relief,
            divergent_relief=source.divergent_relief,
            transform_relief=source.transform_relief,
            shear_relief=source.shear_relief,
            tectonic_relief=source.tectonic_relief,
            impact_relief=impact,
            terrain_variation=variation,
            elevation=total,
        )
