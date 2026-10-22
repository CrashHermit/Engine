"""Elevation fractions and dimensionless volcanic diagnostics."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample


@dataclass(frozen=True, slots=True)
class SourceElevationSample:
    """Coastal, tectonic, and volcanic source-space elevation components."""

    coastal_elevation: np.ndarray
    volcanic_potential: np.ndarray
    volcanic_strength: np.ndarray
    volcanic_relief: np.ndarray
    convergent_relief: np.ndarray
    divergent_relief: np.ndarray
    transform_relief: np.ndarray
    shear_relief: np.ndarray
    tectonic_relief: np.ndarray
    total: np.ndarray


@dataclass(frozen=True, slots=True)
class SourceElevationGradientSample:
    """Independently accessible source contributions and their XYZ gradients."""

    coastal_elevation: ScalarSample
    volcanic_potential: ScalarSample
    volcanic_strength: ScalarSample
    volcanic_relief: ScalarSample
    convergent_relief: ScalarSample
    divergent_relief: ScalarSample
    transform_relief: ScalarSample
    shear_relief: ScalarSample
    tectonic_relief: ScalarSample
    total: ScalarSample


@dataclass(frozen=True, slots=True)
class ElevationResult:
    """Sampled source contributions and final world-space elevation fractions."""

    coastal_elevation: np.ndarray
    volcanic_potential: np.ndarray
    volcanic_strength: np.ndarray
    volcanic_relief: np.ndarray
    convergent_relief: np.ndarray
    divergent_relief: np.ndarray
    transform_relief: np.ndarray
    shear_relief: np.ndarray
    tectonic_relief: np.ndarray
    terrain_variation: np.ndarray
    elevation: np.ndarray
