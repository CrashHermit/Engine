import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.config.worldgen_config import InsolationConfig
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array

def insolation_field(
    *,
    geometry: MeshGeometry,
    cfg: InsolationConfig,
    wobble_noise: FractalField | None = None,
) -> Float64Array:
    """Authored energy field in [0, 1]: hot ring at y = 0, cold ring opposite."""
    height = geometry.height
    sites_y = geometry.sites[:, 1]

    if wobble_noise is not None and cfg.wobble > 0.0:
        sites_y = sites_y + noise(x, y) * cfg.wobble * height

    phase = 2 * pi * sites_y / height * cfg.bands
    insolation = (np.cos(phase) + 1.0) / 2.0
    insolation = 0.5 + (insolation - 0.5) * cfg.contrast

    return insolation
