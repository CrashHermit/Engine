"""Scalar trench and overriding-arc evaluation for compiled source reductions."""

from numba.extending import register_jitable

from src.worldgen.elevation.profiles import subduction_profile


@register_jitable
def subduction_value(signed_distance, parameters, peak, arc_variation):
    """Evaluate the existing finite-support trench/arc response."""
    width, height, trench_width, arc_offset, arc_width, arc_height, trench_depth = (
        parameters
    )
    if abs(signed_distance) >= width:
        return 0.0
    profile = subduction_profile(
        signed_distance,
        width,
        trench_width,
        arc_offset,
        arc_width,
        arc_height,
        arc_variation,
        trench_depth,
    )
    return profile * peak * height
