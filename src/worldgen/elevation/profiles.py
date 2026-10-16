"""Normalized collision, divergent, and subduction relief profiles."""

from src.worldgen.utilities.curves import smoothstep


def clamp_unit(value: float) -> float:
    """Clamp a scalar profile coordinate to its unit support interval."""
    return min(max(value, 0.0), 1.0)


def collision_profile(
    distance: float, width: float, crest_width_fraction: float
) -> tuple[float, float]:
    """Return normalized broad mountain response and squared crest weight."""
    broad = float(smoothstep(1.0 - distance / width))
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
    axial_input = clamp_unit(1.0 - t / axial_width_fraction)
    broad = broad_input * broad_input * (3.0 - 2.0 * broad_input)
    axial = axial_input * axial_input * (3.0 - 2.0 * axial_input)
    signed_axial = divergent_response(continental) * axial_depth_multiplier * axial
    if continental:
        shoulders = shoulder_height_multiplier * 4.0 * t * (1.0 - t) * broad
        return shoulders + signed_axial
    return broad - signed_axial


def subduction_profile(
    distance: float,
    width: float,
    subducting: bool,
    *,
    trench_width_fraction: float = 0.2,
    arc_offset_fraction: float = 0.25,
    arc_width_fraction: float = 0.2,
    arc_height_multiplier: float = 1.5,
) -> float:
    """Return normalized trench or volcanic-arc relief from a source."""
    if width <= 0.0:
        return 0.0
    if subducting:
        return -float(smoothstep(1.0 - distance / (width * trench_width_fraction)))
    arc_position = distance / width
    arc_input = 1.0 - abs(arc_position - arc_offset_fraction) / arc_width_fraction
    return arc_height_multiplier * float(smoothstep(arc_input))
