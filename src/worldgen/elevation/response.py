"""Per-pair geological relief profiles for continuous Cartesian composition.

Distances and widths share source-space units; heights use consumer units.
Strengths are raw motion components, not influence-weighted aggregates. These
profiles include local shape falloff, but not pair-overlap influence; the
response consumer applies that influence exactly once.
"""

import numpy as np
from numba import njit

from src.worldgen.elevation.collision import collision_value
from src.worldgen.elevation.divergence import divergence_value
from src.worldgen.elevation.shear import shear_value
from src.worldgen.elevation.subduction import subduction_value
from src.worldgen.elevation.transform import transform_value


@njit(cache=True)
def collision_relief(
    distances: np.ndarray,
    convergence: np.ndarray,
    width: float,
    height: float,
    crest_width_fraction: float = 0.3,
    crest_height_multiplier: float = 2.0,
) -> np.ndarray:
    """Broad collision uplift with an independently weighted narrow crest."""
    result = np.empty(len(distances), dtype=np.float64)
    parameters = (width, height, crest_width_fraction, crest_height_multiplier)
    for i in range(len(distances)):
        result[i] = collision_value(distances[i], parameters, convergence[i])
    return result


@njit(cache=True)
def continental_rift_relief(
    distances: np.ndarray,
    divergence: np.ndarray,
    width: float,
    height: float,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
    shoulder_height_multiplier: float = 0.35,
) -> np.ndarray:
    """Negative axial rift with positive flanking shoulders."""
    result = np.empty(len(distances), dtype=np.float64)
    parameters = (
        width,
        height,
        axial_width_fraction,
        axial_depth_multiplier,
        shoulder_height_multiplier,
    )
    for i in range(len(distances)):
        result[i] = divergence_value(distances[i], parameters, divergence[i], True)
    return result


@njit(cache=True)
def oceanic_ridge_relief(
    distances: np.ndarray,
    divergence: np.ndarray,
    width: float,
    height: float,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
) -> np.ndarray:
    """Broad positive ridge with a central axial depression, not a trench."""
    result = np.empty(len(distances), dtype=np.float64)
    parameters = (width, height, axial_width_fraction, axial_depth_multiplier, 0.0)
    for i in range(len(distances)):
        result[i] = divergence_value(distances[i], parameters, divergence[i], False)
    return result


@njit(cache=True)
def subduction_relief(
    signed_distances: np.ndarray,
    convergence: np.ndarray,
    width: float,
    height: float,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    trench_depth_multiplier: float = 1.0,
) -> np.ndarray:
    """Trench at zero and arc on the positive (overriding) side.

    The consumer supplies polarity: negative is the descending side. These
    are signed source-face distances, not distances signed by motion direction.
    """
    result = np.empty(len(signed_distances), dtype=np.float64)
    parameters = (
        width,
        height,
        trench_width_fraction,
        arc_offset_fraction,
        arc_width_fraction,
        arc_height_multiplier,
        trench_depth_multiplier,
    )
    for i in range(len(signed_distances)):
        result[i] = subduction_value(
            signed_distances[i], parameters, convergence[i], 1.0
        )
    return result


@njit(cache=True)
def shear_relief(
    distances: np.ndarray,
    shear: np.ndarray,
    width: float,
    height: float,
) -> np.ndarray:
    """Compact fault-zone relief driven by supplied shear strength."""
    result = np.empty(len(distances), dtype=np.float64)
    for i in range(len(distances)):
        result[i] = shear_value(distances[i], (width, height), shear[i])
    return result


@njit(cache=True)
def transform_relief(
    distances: np.ndarray,
    signed_strength: np.ndarray,
    width: float,
    height: float,
) -> np.ndarray:
    """Compact uplift/subsidence from consumer-supplied oblique strength.

    Use transform_strength with closing-positive normal motion if desired.
    Do not add a second full shear contribution unless intentionally blending.
    """
    result = np.empty(len(distances), dtype=np.float64)
    for i in range(len(distances)):
        result[i] = transform_value(distances[i], (width, height), signed_strength[i])
    return result
