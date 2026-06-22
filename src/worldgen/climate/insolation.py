import numpy as np

from src.worldgen.config.worldgen_config import InsolationConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array


def insolation_field(
    *,
    geometry: MeshGeometry,
    cfg: InsolationConfig,
    wobble_noise: FractalField | None = None,
) -> Float64Array:
    """Authored energy field in [0, 1]: hot ring at y = 0, cold ring opposite.

    Args:
        geometry: Torus mesh geometry (sites, width, height).
        cfg: Insolation parameters (bands, contrast, wobble).
        wobble_noise: Optional low-frequency FBm noise to warp ring lines.

    Returns:
        Per-cell insolation in [0, 1].
    """
    height: float = geometry.height
    sites_y: Float64Array = geometry.sites[:, 1]

    # --- Optional noise warp on the Y coordinate ---------------------------
    if wobble_noise is not None and cfg.wobble > 0.0:
        span: float = min(geometry.width, geometry.height)
        frequency: float = 2.0 / span

        xs: Float64Array = geometry.sites[:, 0]
        warp: Float64Array = np.fromiter(
            iter=(
                wobble_noise.sample(x=float(x), y=float(y), frequency=frequency)
                for x, y in zip(xs, sites_y)
            ),
            dtype=np.float64,
            count=geometry.n_cells,
        )
        sites_y = sites_y + warp * cfg.wobble * height

    # --- Core insolation ---------------------------------------------------
    phase: Float64Array = 2.0 * np.pi * sites_y / height * cfg.bands
    insolation: Float64Array = (np.cos(phase) + 1.0) / 2.0
    insolation = 0.5 + (insolation - 0.5) * cfg.contrast

    return insolation
