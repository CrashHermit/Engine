"""Settings for sampled surface measurements."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SurfaceConfig:
    """Fixed measurement footprint as a percentage of planetary circumference."""

    footprint_circumference_percent: float = 0.05
