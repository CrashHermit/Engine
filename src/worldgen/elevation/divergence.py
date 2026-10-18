"""Scalar ridge, axial-valley and shoulder evaluation for compiled reductions."""

from numba.extending import register_jitable

from src.worldgen.elevation.profiles import divergent_profile


@register_jitable
def divergence_value(distance, parameters, peak, continental):
    """Evaluate the existing material-specific divergent response."""
    width, height, axial_width, axial_depth, shoulder_height = parameters
    if distance >= width:
        return 0.0
    profile = divergent_profile(
        distance, width, continental, axial_width, axial_depth, shoulder_height
    )
    return profile * peak * height
