import numpy as np

from src.worldgen.config.worldgen_config import WindConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array
from src.worldgen.workspace import Workspace
from src.worldgen.geometry.field_ops import diffuse
from src.worldgen.noise.rng import FIELD_WIND_U
from src.worldgen.noise.rng import FIELD_WIND_V


def wind_belts(
    *,
    geometry: MeshGeometry,
    cfg: WindConfig,
    latitude: Float64Array,
    turbulence_u: FractalField,
    turbulence_v: FractalField,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Return (wind_u, wind_v, wind_magnitude): three-cell belts + FBm turbulence.

    Earth's banded circulation, as a function of latitude (``L = |latitude|``,
    0 at the equator, 1 at the pole), split into three cells per hemisphere:

    * **Hadley** (``L`` in 0..1/3): tropical **easterlies** (trade winds),
      surface flow toward the equator.
    * **Ferrel** (1/3..2/3): mid-latitude **westerlies**, surface flow toward
      the pole.
    * **Polar** (2/3..1): **polar easterlies**, surface flow toward the equator.

    ``band = sin(3*pi*L)`` is positive on the Hadley/Polar cells and negative on
    the Ferrel cell, so it carries both the easterly/westerly sign (zonal) and
    the toward-equator/toward-pole sign (meridional) at once, going to zero at
    the calm belts (equatorial doldrums, subtropical highs ~30 deg, subpolar
    lows ~60 deg, poles).  A torus has no rotation axis, so belt *directions*
    are authored from latitude rather than derived from Coriolis.

    All terms are functions of latitude only, so the field wraps seamlessly
    around both torus seams.

    Args:
        geometry: Torus mesh with sites and dimensions.
        cfg: Wind parameters (zonal/meridional strength, turbulence).
        latitude: Signed latitude in ``[-1, 1]`` (0 equator, +/-1 poles).
        turbulence_u: FBm noise field for the u-component wobble.
        turbulence_v: FBm noise field for the v-component wobble.

    Returns:
        Tuple of (wind_u, wind_v, wind_magnitude), each shape (n_cells,).
        Where wind_magnitude > 0, (wind_u, wind_v) is unit-length.
    """
    sites: Float64Array = geometry.sites
    xs: Float64Array = sites[:, 0]
    ys: Float64Array = sites[:, 1]
    width: float = geometry.width
    height: float = geometry.height

    # --- three-cell zonal belts (function of latitude only) ---
    lat_abs: Float64Array = np.abs(latitude)
    hemi: Float64Array = np.sign(latitude)  # +1 north, -1 south; 0 at equator
    band: Float64Array = np.sin(3.0 * np.pi * lat_abs)
    # Easterly trades / westerlies / polar easterlies (negative u = easterly).
    base_u: Float64Array = -cfg.zonal_strength * band
    # Toward-equator (Hadley/Polar) vs toward-pole (Ferrel); hemi maps to +/-y.
    base_v: Float64Array = cfg.meridional_strength * band * hemi

    # --- turbulence ---
    # Sample noise at every site; frequency relative to torus size.
    frequency: float = 4.0 / max(width, height)
    turb_u: Float64Array = turbulence_u.sample_array(
        xs=xs, ys=ys, frequency=frequency,
    ) * cfg.turbulence
    turb_v: Float64Array = turbulence_v.sample_array(
        xs=xs, ys=ys, frequency=frequency,
    ) * cfg.turbulence

    # --- add turbulence then normalize ---
    wind_u: Float64Array = base_u + turb_u
    wind_v: Float64Array = base_v + turb_v

    mag: Float64Array = np.hypot(wind_u, wind_v)
    wind_u = np.where(mag > 0.0, wind_u / mag, 0.0)
    wind_v = np.where(mag > 0.0, wind_v / mag, 0.0)
    wind_magnitude: Float64Array = mag

    return wind_u, wind_v, wind_magnitude


def elevation_gradient(
    *,
    geometry: MeshGeometry,
    elevation: Float64Array,
) -> tuple[Float64Array, Float64Array]:
    """Per-cell uphill gradient (grad_x, grad_y) via distance-weighted neighbor sum.

    For cell i: grad = sum_j  (z[j] - z[i]) / |d_ij|^2  *  d_ij
    summed over neighbors j, where d_ij is the torus-aware site offset.
    This weighted sum points uphill.

    Args:
        geometry: Torus mesh with CSR adjacency.
        elevation: Per-cell elevation in [0, 1].

    Returns:
        Tuple of (grad_x, grad_y), each shape (n_cells,).
    """
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = geometry.n_cells

    grad_x: Float64Array = np.zeros(shape=n, dtype=np.float64)
    grad_y: Float64Array = np.zeros(shape=n, dtype=np.float64)

    for cell_id in range(n):
        z_i: float = float(elevation[cell_id])
        site_i: Float64Array = sites[cell_id]

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id_int: int = int(neighbor_id)
            z_j: float = float(elevation[neighbor_id_int])
            site_j: Float64Array = sites[neighbor_id_int]

            # Torus-aware displacement from i to j.
            d: Float64Array = torus_delta(a=site_i, b=site_j, width=width, height=height)
            dist_sq: float = float(d[0] ** 2 + d[1] ** 2)

            if dist_sq < 1e-12:
                # Skip zero-length (shouldn't happen, but guard).
                continue

            # Weighted contribution pointing uphill.
            weight: float = (z_j - z_i) / dist_sq
            grad_x[cell_id] += weight * float(d[0])
            grad_y[cell_id] += weight * float(d[1])

    return grad_x, grad_y


def wind_divergence(
    *,
    geometry: MeshGeometry,
    vel_u: Float64Array,
    vel_v: Float64Array,
) -> Float64Array:
    """Per-cell scalar divergence of the wind velocity field, ``∇·w``.

    The divergence-flavoured analogue of :func:`elevation_gradient`: instead of
    accumulating a vector that points uphill, we accumulate the scalar

        div_i = Σ_j  (w_j − w_i) · d_ij  /  |d_ij|²

    over torus-aware neighbour offsets ``d_ij``.  ``> 0`` means the wind speeds
    up in the outward direction (**divergence**); ``< 0`` means it slows or
    reverses toward the cell (**convergence**, where air piles up and rises).

    Args:
        geometry: Torus mesh with CSR adjacency.
        vel_u: Wind velocity x-component per cell (direction × speed).
        vel_v: Wind velocity y-component per cell.

    Returns:
        Per-cell divergence, shape ``(n_cells,)``.
    """
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = geometry.n_cells

    divergence: Float64Array = np.zeros(shape=n, dtype=np.float64)

    for cell_id in range(n):
        wu_i: float = float(vel_u[cell_id])
        wv_i: float = float(vel_v[cell_id])
        site_i: Float64Array = sites[cell_id]
        acc: float = 0.0

        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id_int: int = int(neighbor_id)
            d: Float64Array = torus_delta(
                a=site_i, b=sites[neighbor_id_int], width=width, height=height
            )
            dist_sq: float = float(d[0] ** 2 + d[1] ** 2)
            if dist_sq < 1e-12:
                continue
            du: float = float(vel_u[neighbor_id_int]) - wu_i
            dv: float = float(vel_v[neighbor_id_int]) - wv_i
            acc += (du * float(d[0]) + dv * float(d[1])) / dist_sq

        divergence[cell_id] = acc

    return divergence


def convergence_field(
    *,
    divergence: Float64Array,
    percentile: float,
) -> Float64Array:
    """Signed vertical-motion field in ``[-1, 1]`` from wind divergence.

    Rising air is ``-divergence``: positive where the wind converges (air piles
    up and rises → rain) and negative where it diverges (descending, subsiding
    air → drying, the subtropical deserts).  Scaled symmetrically so a high
    percentile of ``|rising|`` maps to magnitude 1.0 — a stable per-seed
    normalization, the same idiom used for slope/rain-out.

    The signed form lets a single field carry the *whole* latitudinal banding:
    the wet ITCZ/subpolar belts and the dry subtropics, where pure convergence
    (the rising half alone) could only add wet and never suppress it.

    Args:
        divergence: Per-cell ``∇·w`` from :func:`wind_divergence`.
        percentile: ``|rising|`` percentile mapped to magnitude 1.0.

    Returns:
        Per-cell signed vertical motion in ``[-1, 1]`` (+ rising, − sinking).
    """
    rising: Float64Array = -divergence
    anchor: float = float(np.percentile(np.abs(rising), percentile))
    if anchor > 0.0:
        rising = np.clip(rising / anchor, -1.0, 1.0)
    return rising


def deflect_wind(
    *,
    wind_u: Float64Array,
    wind_v: Float64Array,
    wind_magnitude: Float64Array,
    grad_x: Float64Array,
    grad_y: Float64Array,
    cfg: WindConfig,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Bend wind around uphill terrain and slow it where it is blocked.

    Wind blows harder into uphill terrain; deflection pushes it sideways along
    ranges and accelerates it through gaps.  The deflected unit vector's length
    is a natural *deflection factor* in ``[0, 1]`` — ``1`` where the wind passes
    unobstructed (flat ground or wind parallel to the slope) and shrinking as
    terrain turns it — so the incoming belt speed is scaled by that factor.  The
    previous version discarded the belt speed and reported the factor itself as
    the magnitude, which pinned every flat cell to exactly ``1.0``.

    Args:
        wind_u: East-west wind direction (unit vector, may be zero-magnitude).
        wind_v: North-south wind direction (unit vector, may be zero-magnitude).
        wind_magnitude: Incoming belt wind speed per cell.
        grad_x: X-component of elevation gradient (points uphill).
        grad_y: Y-component of elevation gradient (points uphill).
        cfg: Wind deflection strength.

    Returns:
        Tuple of ``(wind_u, wind_v, wind_magnitude)``: unit direction after
        deflection, and belt speed scaled by the deflection factor.
    """
    # --- gradient magnitude and unit direction ---
    grad_mag: Float64Array = np.hypot(grad_x, grad_y)
    grad_u: Float64Array = np.where(grad_mag > 0.0, grad_x / grad_mag, 0.0)
    grad_v: Float64Array = np.where(grad_mag > 0.0, grad_y / grad_mag, 0.0)

    # --- dot product: how much wind blows into uphill ---
    into_slope: Float64Array = np.maximum(0.0, wind_u * grad_u + wind_v * grad_v)

    # --- subtract uphill component ---
    deflected_u: Float64Array = wind_u - cfg.deflection * into_slope * grad_u
    deflected_v: Float64Array = wind_v - cfg.deflection * into_slope * grad_v

    # --- deflection factor (<= 1) scales the belt speed; renormalize direction ---
    deflection_factor: Float64Array = np.hypot(deflected_u, deflected_v)
    safe: Float64Array = deflection_factor > 0.0
    wind_u = np.where(safe, deflected_u / deflection_factor, 0.0)
    wind_v = np.where(safe, deflected_v / deflection_factor, 0.0)
    wind_magnitude = wind_magnitude * deflection_factor

    return wind_u, wind_v, wind_magnitude


class WindStage:
    """Compute wind belts and terrain deflection.

    Pipeline order: ``Insolation → Wind → OceanCurrent → Temperature → Moisture``.
    Wind precedes the ocean-current and temperature stages because the current
    is wind-advected and coasts moderate toward the wind-borne sea temperature.
    """

    reads: tuple[str, ...] = ("elevation", "latitude")
    writes: tuple[str, ...] = ("convergence", "wind_magnitude", "wind_u", "wind_v")

    def run(self, ctx: Workspace) -> None:
        """Compute wind fields and write ``ctx.fields.wind_u/v/magnitude``."""
        cfg: WindConfig = ctx.config.wind

        # --- prerequisites ---
        geometry = ctx.geometry

        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before WindStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        latitude_field: Float64Array | None = ctx.fields.latitude
        if latitude_field is None:
            msg = "latitude must be set before WindStage"
            raise RuntimeError(msg)
        latitude: Float64Array = latitude_field

        # --- turbulence noise fields (two independent sub-seeded sources) ---
        turbulence_u: FractalField = FractalField(
            sampler=ctx.noise_for("wind_u"),
            field_id=FIELD_WIND_U,
            octaves=3,
        )
        turbulence_v: FractalField = FractalField(
            sampler=ctx.noise_for("wind_v"),
            field_id=FIELD_WIND_V,
            octaves=3,
        )

        # --- step 3: wind belts ---
        wind_u, wind_v, wind_magnitude = wind_belts(
            geometry=geometry,
            cfg=cfg,
            latitude=latitude,
            turbulence_u=turbulence_u,
            turbulence_v=turbulence_v,
        )

        # --- step 4: terrain deflection ---
        grad_x, grad_y = elevation_gradient(
            geometry=ctx.geometry,
            elevation=elevation,
        )

        wind_u, wind_v, wind_magnitude = deflect_wind(
            wind_u=wind_u,
            wind_v=wind_v,
            wind_magnitude=wind_magnitude,
            grad_x=grad_x,
            grad_y=grad_y,
            cfg=cfg,
        )

        # --- normalize speed to [0, 1] (belt speed × deflection) ---
        mag_max: float = float(wind_magnitude.max())
        if mag_max > 0.0:
            wind_magnitude = wind_magnitude / mag_max

        # --- convergence of the wind velocity field (rising air → rain) ---
        # Divergence is computed on the full velocity (unit direction × speed) so
        # the calm, converging doldrums read as strong convergence.
        divergence: Float64Array = wind_divergence(
            geometry=geometry,
            vel_u=wind_u * wind_magnitude,
            vel_v=wind_v * wind_magnitude,
        )
        convergence: Float64Array = convergence_field(
            divergence=divergence, percentile=cfg.convergence_percentile
        )
        # Smooth to a climatic normal: drop turbulence-scale noise, keep the
        # belt/terrain-scale convergence that bands the rain.
        convergence = diffuse(
            geometry=geometry,
            field=convergence,
            strength=cfg.convergence_smoothing_strength,
            passes=cfg.convergence_smoothing_passes,
        )

        # --- write results ---
        ctx.fields.wind_u = wind_u
        ctx.fields.wind_v = wind_v
        ctx.fields.wind_magnitude = wind_magnitude
        ctx.fields.convergence = convergence
