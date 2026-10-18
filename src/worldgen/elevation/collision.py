"""Scalar continental-collision evaluation shared by compiled source reductions."""

from numba.extending import register_jitable

from src.worldgen.elevation.profiles import collision_profile


@register_jitable
def collision_value(distance, parameters, peak):
    """Evaluate broad uplift and a narrow crest without temporary arrays."""
    width, height, crest_width, crest_height = parameters
    if distance >= width:
        return 0.0
    broad, crest = collision_profile(distance, width, crest_width)
    return peak * (broad + crest_height * crest) * height
