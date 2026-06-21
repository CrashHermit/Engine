from __future__ import annotations

import numpy as np

from src.worldgen.config.worldgen_config import WindConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array, Int32Array


def wind_belts(
    *,
    geometry: MeshGeometry,
    cfg: WindConfig,
    turbulence_u: FractalField,
    turbulence_v: FractalField,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Return (wind_u, wind_v, wind_magnitude): zonal belts + FBm turbulence, normalized.

    Computes sinusoidal zonal wind belts that wrap seamlessly around the torus,
    adds independent FBm turbulence per component, then normalizes to store
    unit direction in (wind_u, wind_v) and speed in wind_magnitude.

    Args:
        geometry: Torus mesh with sites and dimensions.
        cfg: Wind parameters (belt_count, meridional_strength, turbulence).
        turbulence_u: FBm noise field for the u-component wobble.
        turbulence_v: FBm noise field for the v-component wobble.

    Returns:
        Tuple of (wind_u, wind_v, wind_magnitude), each shape (n_cells,).
        Where wind_magnitude > 0, (wind_u, wind_v) is unit-length.
    """
    sites: Float64Array = geometry.sites
    xs: Float64Array = sites[:, 0]
    ys: Float64Array = sites[:, 1]
    n: int = geometry.n_cells
    width: float = geometry.width
    height: float = geometry.height

    # --- zonal belts ---
    # Phase wraps correctly: 2*pi*y/height ensures y=0 == y=height.
    phase: Float64Array = 2.0 * np.pi * ys / height * cfg.belt_count
    base_u: Float64Array = -np.cos(phase)  # zonal east-west belts
    base_v: Float64Array = np.sin(phase) * cfg.meridional_strength  # meridional

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


def deflect_wind(
    *,
    wind_u: Float64Array,
    wind_v: Float64Array,
    grad_x: Float64Array,
    grad_y: Float64Array,
    cfg: WindConfig,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Subtract the uphill-into-slope component from wind; return renormalized (u, v, magnitude).

    Wind blows harder into uphill terrain; deflection pushes it sideways along
    ranges and accelerates it through gaps.

    Args:
        wind_u: East-west wind direction (unit vector, may be zero-magnitude).
        wind_v: North-south wind direction (unit vector, may be zero-magnitude).
        grad_x: X-component of elevation gradient (points uphill).
        grad_y: Y-component of elevation gradient (points uphill).
        cfg: Wind deflection strength.

    Returns:
        Tuple of (wind_u, wind_v, wind_magnitude), renormalized after deflection.
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

    # --- renormalize ---
    mag: Float64Array = np.hypot(deflected_u, deflected_v)
    wind_u = np.where(mag > 0.0, deflected_u / mag, 0.0)
    wind_v = np.where(mag > 0.0, deflected_v / mag, 0.0)
    wind_magnitude: Float64Array = mag

    return wind_u, wind_v, wind_magnitude
