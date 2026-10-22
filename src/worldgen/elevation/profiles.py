"""Normalized elevation relief profiles and compact source shapes."""

from numba.extending import register_jitable
import numpy as np

from src.worldgen.utilities.curves import clamp_unit, smoothstep, smoothstep_scalar


def coastal_height_profile(
    margin_distance: np.ndarray,
    *,
    inland_width: np.ndarray,
    shelf_width: np.ndarray,
    slope_width: np.ndarray,
    interior_height: np.ndarray | float,
    shelf_depth: np.ndarray | float,
    basin_depth: np.ndarray | float,
) -> np.ndarray:
    """Return relief from a scalar coordinate and profile widths in matching units."""
    distance = shelf_width - margin_distance
    inland = smoothstep((distance + inland_width) / inland_width)
    shelf = smoothstep(distance / shelf_width)
    slope = smoothstep((distance - shelf_width) / slope_width)
    return (
        interior_height * (1.0 - inland)
        - shelf_depth * shelf
        - (basin_depth - shelf_depth) * slope
    )


@register_jitable
def smoothstep_derivative(value: float) -> float:
    """Return the derivative of clamped cubic smoothstep."""
    if value <= 0.0 or value >= 1.0:
        return 0.0
    return 6.0 * value * (1.0 - value)


@register_jitable
def transform_profile_with_partials(
    distance: float, width: float
) -> tuple[float, float, float]:
    """Return attenuation and partials with respect to distance and width."""
    value = transform_profile(distance, width)
    if width <= 0.0:
        return value, 0.0, 0.0
    argument = 1.0 - distance / width
    slope = smoothstep_derivative(argument)
    return value, -slope / width, slope * distance / (width * width)


@register_jitable
def shear_profile_with_partials(
    distance: float, width: float
) -> tuple[float, float, float]:
    """Return attenuation and partials with respect to distance and width."""
    return transform_profile_with_partials(distance, width)


@register_jitable
def collision_profile_with_partials(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float, float, float]:
    """Return broad/crest profiles and their distance derivatives."""
    if width <= 0.0:
        return 0.0, 0.0, 0.0, 0.0
    broad = smoothstep_scalar(1.0 - distance / width)
    crest_input = distance / (width * crest_width_fraction)
    crest_complement = 1.0 - smoothstep_scalar(crest_input)
    crest = crest_complement * crest_complement
    broad_derivative = -smoothstep_derivative(1.0 - distance / width) / width
    crest_derivative = (
        -2.0
        * crest_complement
        * smoothstep_derivative(crest_input)
        / (width * crest_width_fraction)
    )
    return broad, crest, broad_derivative, crest_derivative


@register_jitable
def collision_profile_with_full_partials(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float, float, float, float, float, float]:
    """Return both profiles and their distance, width, and crest-fraction partials."""
    broad, crest, broad_d_distance, crest_d_distance = collision_profile_with_partials(
        distance, width, crest_width_fraction
    )
    if width <= 0.0:
        return broad, crest, 0.0, 0.0, 0.0, 0.0, 0.0
    broad_input = 1.0 - distance / width
    broad_d_width = smoothstep_derivative(broad_input) * distance / (width * width)
    crest_complement = 1.0 - smoothstep_scalar(
        distance / (width * crest_width_fraction)
    )
    crest_slope = smoothstep_derivative(distance / (width * crest_width_fraction))
    crest_d_width = (
        2.0
        * crest_complement
        * crest_slope
        * distance
        / (width * width * crest_width_fraction)
    )
    crest_d_fraction = (
        2.0
        * crest_complement
        * crest_slope
        * distance
        / (width * crest_width_fraction * crest_width_fraction)
    )
    return (
        broad,
        crest,
        broad_d_distance,
        crest_d_distance,
        broad_d_width,
        crest_d_width,
        crest_d_fraction,
    )


@register_jitable
def divergent_profile_with_partials(
    distance: float,
    width: float,
    continental: bool,
    axial_width_fraction: float = 0.25,
    axial_depth_multiplier: float = 0.65,
    shoulder_height_multiplier: float = 0.35,
) -> tuple[float, float]:
    """Return divergent relief and its distance derivative."""
    if width <= 0.0 or distance >= width:
        return 0.0, 0.0
    t = clamp_unit(distance / width)
    broad_input = 1.0 - t
    axial_input = 1.0 - t / axial_width_fraction
    broad = smoothstep_scalar(broad_input)
    axial = smoothstep_scalar(axial_input)
    broad_dt = -smoothstep_derivative(broad_input)
    axial_dt = -smoothstep_derivative(axial_input) / axial_width_fraction
    signed_axial = divergent_response(continental) * axial_depth_multiplier * axial
    signed_axial_dt = (
        divergent_response(continental) * axial_depth_multiplier * axial_dt
    )
    if continental:
        shoulder_base = 16.0 * t * t * (1.0 - t) * (1.0 - t)
        shoulder_dt = 32.0 * t * (1.0 - t) * (1.0 - 2.0 * t)
        value = shoulder_height_multiplier * shoulder_base * broad + signed_axial
        derivative_t = (
            shoulder_height_multiplier
            * (shoulder_dt * broad + shoulder_base * broad_dt)
            + signed_axial_dt
        )
    else:
        value = broad - signed_axial
        derivative_t = broad_dt - signed_axial_dt
    return value, derivative_t / width


@register_jitable
def subduction_profile_with_partials(
    signed_distance: float,
    width: float,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    arc_variation: float = 1.0,
    trench_depth_multiplier: float = 1.0,
) -> tuple[float, float, float, float]:
    """Return relief and partials by signed distance, width, and arc variation."""
    value = subduction_profile(
        signed_distance,
        width,
        trench_width_fraction,
        arc_offset_fraction,
        arc_width_fraction,
        arc_height_multiplier,
        arc_variation,
        trench_depth_multiplier,
    )
    if width <= 0.0:
        return value, 0.0, 0.0, 0.0
    trench_scale = width * trench_width_fraction
    trench_input = 1.0 - abs(signed_distance) / trench_scale
    trench_slope = smoothstep_derivative(trench_input)
    trench_d_distance = (
        trench_depth_multiplier
        * trench_slope
        * (1.0 if signed_distance > 0.0 else -1.0)
        / trench_scale
    )
    trench_d_width = (
        -trench_depth_multiplier
        * trench_slope
        * abs(signed_distance)
        / (width * width * trench_width_fraction)
    )
    if signed_distance <= 0.0:
        return value, trench_d_distance, trench_d_width, 0.0
    arc_position = signed_distance / width
    arc_input = 1.0 - abs(arc_position - arc_offset_fraction) / arc_width_fraction
    arc_abs_sign = 1.0 if arc_position > arc_offset_fraction else -1.0
    arc_profile = smoothstep_scalar(arc_input)
    arc_profile_d_position = (
        -smoothstep_derivative(arc_input) * arc_abs_sign / arc_width_fraction
    )
    forearc_input = arc_position / arc_offset_fraction
    forearc = smoothstep_scalar(forearc_input)
    forearc_d_position = smoothstep_derivative(forearc_input) / arc_offset_fraction
    arc_product = arc_profile * forearc
    arc_d_position = arc_profile_d_position * forearc + arc_profile * forearc_d_position
    arc_scale = arc_height_multiplier * arc_variation
    return (
        value,
        trench_d_distance + arc_scale * arc_d_position / width,
        trench_d_width - arc_scale * arc_d_position * arc_position / width,
        arc_height_multiplier * arc_product,
    )


@register_jitable
def transform_profile(distance: float, width: float) -> float:
    """Return compact smoothstep attenuation across transform relief width."""
    if width <= 0.0:
        return 0.0
    return smoothstep_scalar(1.0 - distance / width)


@register_jitable
def shear_profile(distance: float, width: float) -> float:
    """Return compact smoothstep attenuation across a pure-shear fault zone."""
    if width <= 0.0:
        return 0.0
    return smoothstep_scalar(1.0 - distance / width)


@register_jitable
def collision_profile(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float]:
    """Return normalized broad mountain response and squared crest weight."""
    broad = smoothstep_scalar(1.0 - distance / width)
    crest_weight = 1.0 - smoothstep_scalar(distance / (width * crest_width_fraction))
    return broad, crest_weight**2


@register_jitable
def divergent_response(continental: bool) -> float:
    """Return the sign of divergent axial relief for a crust type."""
    return -1.0 if continental else 1.0


@register_jitable
def divergent_profile(
    distance: float,
    width: float,
    continental: bool,
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
        shoulders = (
            shoulder_height_multiplier * 16.0 * t * t * (1.0 - t) * (1.0 - t) * broad
        )
        return shoulders + signed_axial
    return broad - signed_axial


@register_jitable
def subduction_profile(
    signed_distance: float,
    width: float,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
    arc_variation: float = 1.0,
    trench_depth_multiplier: float = 1.0,
) -> float:
    """Return continuous relief: negative distance descends, positive overrides.

    The trench depth and overriding arc amplitude are independently scaled.
    """
    if width <= 0.0:
        return 0.0
    trench = -trench_depth_multiplier * smoothstep_scalar(
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
