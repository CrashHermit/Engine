"""Named source relief and world-space elevation results."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample


@dataclass(frozen=True, slots=True)
class SourceReliefSample:
    """Coastal and tectonic source-space relief components."""

    coastal_elevation: np.ndarray
    convergent_relief: np.ndarray
    divergent_relief: np.ndarray
    transform_relief: np.ndarray
    shear_relief: np.ndarray
    tectonic_relief: np.ndarray
    total: np.ndarray


@dataclass(frozen=True, slots=True)
class SourceReliefGradientSample:
    """Independently accessible source contributions and their XYZ gradients."""

    coastal_elevation: ScalarSample
    convergent_relief: ScalarSample
    divergent_relief: ScalarSample
    transform_relief: ScalarSample
    shear_relief: ScalarSample
    tectonic_relief: ScalarSample
    total: ScalarSample


@dataclass(frozen=True, slots=True)
class ElevationResult:
    """Source relief, world-space impacts and variation, and final elevation."""

    coastal_elevation: np.ndarray
    volcanic_strength: np.ndarray
    volcanic_relief: np.ndarray
    convergent_relief: np.ndarray
    divergent_relief: np.ndarray
    transform_relief: np.ndarray
    shear_relief: np.ndarray
    tectonic_relief: np.ndarray
    impact_relief: np.ndarray
    terrain_variation: np.ndarray
    elevation: np.ndarray
