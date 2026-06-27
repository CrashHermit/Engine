import numpy as np

from src.worldgen.config.worldgen_config import InsolationConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array
from src.worldgen.workspace import Workspace
from src.worldgen.noise.rng import FIELD_INSOLATION_WOBBLE


def _wrapped_yc(
    *,
    geometry: MeshGeometry,
    wobble_noise: FractalField | None,
    cfg: InsolationConfig,
) -> Float64Array:
    """Per-cell normalized torus-y in [0, 1), optionally noise-warped."""
    height: float = geometry.height
    sites_y: Float64Array = geometry.sites[:, 1]

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

    return (sites_y / height) % 1.0


def latitude_field(
    *,
    geometry: MeshGeometry,
    cfg: InsolationConfig,
    wobble_noise: FractalField | None = None,
) -> Float64Array:
    """Signed latitude in [-1, 1]: 0 at the equator (map center), +/-1 at the poles.

    On a torus the y-axis wraps, so we commit the legible semantic: the equator
    sits at the map center (y = height/2) and the poles sit at the y-wrap seam
    (y = 0 == height).  Northern and southern hemispheres are mirror images that
    both lead to the same wrapped polar cap.

    The magnitude ``|latitude|`` (0 equator -> 1 pole) is continuous across the
    seam; the *sign* (hemisphere) flips at the pole, where the magnitude is 1.
    This single-line discontinuity is the inherent "both poles are the same
    wrapped point" artifact of a torus and is invisible in play.  Downstream the
    weather layer reads ``|latitude|`` for seasonal amplitude and the sign for
    hemisphere phase.

    Args:
        geometry: Torus mesh geometry (sites, width, height).
        cfg: Insolation parameters (``bands`` cycles, ``wobble``).
        wobble_noise: Optional low-frequency FBm to warp the latitude lines.

    Returns:
        Per-cell signed latitude in ``[-1, 1]``.
    """
    yc: Float64Array = _wrapped_yc(
        geometry=geometry, wobble_noise=wobble_noise, cfg=cfg
    )
    phase: Float64Array = 2.0 * np.pi * cfg.bands * yc
    lat_abs: Float64Array = 0.5 * (1.0 + np.cos(phase))  # 0 equator, 1 pole
    hemisphere: Float64Array = np.sign(np.sin(phase))  # +1 north, -1 south
    return hemisphere * lat_abs


def insolation_field(
    *,
    geometry: MeshGeometry,
    cfg: InsolationConfig,
    latitude: Float64Array,
) -> Float64Array:
    """Insolation in [0, 1] from latitude: 1 at the equator, 0 at the poles.

    A raw ``1 - |latitude|`` ramp lingers at its extremes, so ``temperate_bias``
    (>1) widens the temperate middle the way most of a planet is temperate, not
    polar/equatorial; ``contrast`` spreads the zones about the mid-value.

    Args:
        geometry: Torus mesh geometry (unused; kept for signature symmetry).
        cfg: Insolation parameters (``temperate_bias``, ``contrast``).
        latitude: Signed latitude in ``[-1, 1]`` from :func:`latitude_field`.

    Returns:
        Per-cell insolation in ``[0, 1]``.
    """
    # Centered energy: +1 at the equator, -1 at the poles.
    centered: Float64Array = 1.0 - 2.0 * np.abs(latitude)

    if cfg.temperate_bias != 1.0:
        centered = np.sign(centered) * np.abs(centered) ** cfg.temperate_bias

    insolation: Float64Array = 0.5 + 0.5 * centered
    insolation = 0.5 + (insolation - 0.5) * cfg.contrast
    return np.clip(insolation, 0.0, 1.0)


class InsolationStage:
    """Compute the signed ``latitude`` driver and the insolation field.

    Pipeline order:
    ``Finalize → Insolation → Wind → OceanCurrent → Temperature → Moisture``
    """

    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ("insolation", "latitude")

    def run(self, ctx: Workspace) -> None:
        """Compute latitude + insolation; write both to ``ctx.fields``."""
        cfg: InsolationConfig = ctx.config.insolation

        # --- prerequisites ---
        geometry = ctx.geometry

        # --- optional wobble noise (warps the latitude lines) ---
        wobble_noise: FractalField | None = None
        if cfg.wobble > 0.0:
            wobble_noise = FractalField(
                sampler=ctx.noise_for("insolation_wobble"),
                field_id=FIELD_INSOLATION_WOBBLE,
                octaves=3,
            )

        # --- compute latitude first, then insolation from it ---
        latitude = latitude_field(
            geometry=geometry, cfg=cfg, wobble_noise=wobble_noise
        )
        ctx.fields.latitude = latitude
        ctx.fields.insolation = insolation_field(
            geometry=geometry, cfg=cfg, latitude=latitude
        )
