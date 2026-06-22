from __future__ import annotations

import numpy as np

from src.worldgen.config.worldgen_config import MoistureConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def build_downwind(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
) -> Int32Array:
    """For each cell, the neighbor whose direction best aligns with the wind.

    Computes the torus-aware displacement vector to each neighbor and picks
    the one with the maximum positive dot product with the cell's wind direction.
    Cells with no downwind-aligned neighbor (or zero wind) get ``-1`` (sink).

    Args:
        geometry: Torus mesh with CSR adjacency.
        wind_u: Unit wind direction x-component (shape ``(n_cells,)``).
        wind_v: Unit wind direction y-component (shape ``(n_cells,)``).

    Returns:
        ``downwind`` array (shape ``(n_cells,)``): the neighbor cell id the
        wind blows toward, or ``-1`` for sinks.
    """
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = geometry.n_cells

    downwind: Int32Array = np.full(n, fill_value=-1, dtype=np.int32)

    for i in range(n):
        wi: float = float(wind_u[i])
        wv: float = float(wind_v[i])

        # Zero wind — no preferred direction; treat as sink.
        if wi == 0.0 and wv == 0.0:
            continue

        best_dot: float = -np.inf
        best_j: int = -1

        for neighbor_id in geometry.neighbors_of(cell_id=i):
            j: int = int(neighbor_id)
            d: Float64Array = torus_delta(
                a=sites[i], b=sites[j], width=width, height=height
            )
            dot: float = float(d[0]) * wi + float(d[1]) * wv
            if dot > best_dot:
                best_dot = dot
                best_j = j

        if best_dot > 0.0:
            downwind[i] = best_j

    return downwind


def transport_moisture(
    *,
    geometry: MeshGeometry,
    downwind: Int32Array,
    temperature: Float64Array,
    elevation: Float64Array,
    is_land: BoolArray,
    cfg: MoistureConfig,
) -> Float64Array:
    """Advect ocean-sourced moisture downwind, raining it out.

    Double-buffered advection loop:
      1. Refill ocean moisture as ``evaporation × temperature``.
      2. For each cell, compute ``rainout`` from base drying, orographic
         forcing (uphill), and temperature chill.
      3. Accumulate rain into ``precipitation[i]``; remainder travels
         to the downwind neighbor.
      4. Swap buffers and repeat for ``cfg.passes`` iterations.

    After the loop, precipitation is normalized by its 99th percentile
    and clipped to ``[0, 1]``.

    Args:
        geometry: Torus mesh (used for cell count).
        downwind: Precomputed downwind neighbor per cell (``-1`` = sink).
        temperature: Per-cell temperature in ``[0, 1]``.
        elevation: Per-cell elevation in ``[-1, 1]``; 0 = sea level.
        is_land: ``True`` for land cells, ``False`` for ocean.
        cfg: Moisture transport parameters.

    Returns:
        ``precipitation`` array in ``[0, 1]``.
    """
    n: int = geometry.n_cells

    moisture: Float64Array = np.zeros(shape=n, dtype=np.float64)
    precipitation: Float64Array = np.zeros(shape=n, dtype=np.float64)

    ocean_mask: BoolArray = ~is_land

    for _ in range(cfg.passes):
        # Refill ocean moisture at the start of every pass.
        moisture[ocean_mask] = cfg.evaporation * temperature[ocean_mask]

        new_moisture: Float64Array = np.zeros(shape=n, dtype=np.float64)

        for i in range(n):
            mi: float = float(moisture[i])
            if mi <= 0.0:
                continue

            j: int = int(downwind[i])
            if j < 0:
                # Sink — moisture evaporates / falls as rain here.
                precipitation[i] += mi
                continue

            uphill: float = max(0.0, float(elevation[j]) - float(elevation[i]))
            chill: float = max(0.0, float(temperature[i]) - float(temperature[j]))
            rainout: float = np.clip(
                cfg.base_rain + cfg.oro * uphill + cfg.chill * chill,
                a_min=0.0,
                a_max=1.0,
            )
            rain: float = mi * rainout

            precipitation[i] += rain
            new_moisture[j] += mi - rain

        moisture = new_moisture

    # Normalize by 99th percentile so a single freak cell doesn't
    # compress the whole scale.
    p99: float = float(np.percentile(a=precipitation, q=99))
    if p99 > 0.0:
        precipitation = precipitation / p99

    return np.clip(precipitation, a_min=0.0, a_max=1.0)
