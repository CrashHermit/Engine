"""Normalized collision, divergent, and subduction relief profiles."""

import numpy as np

from src.worldgen.utilities.curves import clamp_unit, smoothstep, smoothstep_scalar


def shield_profile(distance: np.ndarray | float, width: float) -> np.ndarray | float:
    """Return compact shield attenuation for a positive support width."""
    return smoothstep(1.0 - distance / width)


def transform_profile(distance: float, width: float) -> float:
    """Return compact smoothstep attenuation across transform relief width."""
    if width <= 0.0:
        return 0.0
    return smoothstep_scalar(1.0 - distance / width)


def collision_profile(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float]:
    """Return normalized broad mountain response and squared crest weight."""
    broad = smoothstep_scalar(1.0 - distance / width)
    crest_weight = max(1.0 - distance / (width * crest_width_fraction), 0.0)
    return broad, crest_weight**2


def divergent_response(continental: bool) -> float:
    """Return the sign of divergent axial relief for a crust type."""
    return -1.0 if continental else 1.0


def divergent_profile(
    distance: float,
    width: float,
    continental: bool,
    *,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
    shoulder_height_multiplier: float = 0.35,
) -> float:
    """Return normalized divergent relief at distance from its boundary."""
    if width <= 0.0:
        return 0.0
    t = clamp_unit(distance / width)
    broad_input = 1.0 - t
    axial_input = 1.0 - t / axial_width_fraction
    broad = smoothstep_scalar(broad_input)
    axial = smoothstep_scalar(axial_input)
    signed_axial = divergent_response(continental) * axial_depth_multiplier * axial
    if continental:
        shoulders = shoulder_height_multiplier * 4.0 * t * (1.0 - t) * broad
        return shoulders + signed_axial
    return broad - signed_axial


def subduction_profile(
    signed_distance: float,
    width: float,
    *,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    arc_variation: float = 1.0,
) -> float:
    """Return continuous relief: negative distance descends, positive overrides.

    The trench floor is shared at zero. Only the offset volcanic arc varies.
    """
    if width <= 0.0:
        return 0.0
    trench = -smoothstep_scalar(
        1.0 - abs(signed_distance) / (width * trench_width_fraction)
    )
    if signed_distance <= 0.0:
        return trench
    arc_position = signed_distance / width
    arc_input = 1.0 - abs(arc_position - arc_offset_fraction) / arc_width_fraction
    # Keep volcanic uplift zero at the trench even if its support overlaps zero.
    forearc_rise = smoothstep_scalar(arc_position / arc_offset_fraction)
    arc = arc_height_multiplier * smoothstep_scalar(arc_input) * forearc_rise
    return trench + arc * arc_variation
