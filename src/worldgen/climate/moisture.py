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
) -> tuple[Int32Array, Int32Array, Float64Array]:
    """Per-cell downwind neighbor *distribution*, as a CSR fan.

    Moisture does not travel in a single-file line: it spreads to every
    neighbor the wind pushes toward, weighted by how well that neighbor aligns
    with the wind.  For each cell we keep all neighbors with a positive
    alignment ``dot(unit_offset, wind)`` and normalize their weights to sum to
    one; cells with no downwind-aligned neighbor (or zero wind) are sinks (an
    empty row), where moisture rains out in place.

    Returning a CSR triple (rather than one neighbor per cell) is what turns
    the old 1-D moisture filaments — which left most interior cells bone dry —
    into a spreading front that actually wets the land.

    Args:
        geometry: Torus mesh with CSR adjacency.
        wind_u: Unit wind direction x-component (shape ``(n_cells,)``).
        wind_v: Unit wind direction y-component (shape ``(n_cells,)``).

    Returns:
        ``(indptr, indices, weights)``: CSR arrays over downwind neighbors.
        Row ``i`` spans ``indptr[i]:indptr[i + 1]``; ``indices`` holds the
        neighbor cell ids and ``weights`` their normalized share (summing to
        one per non-sink row).
    """
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = geometry.n_cells

    indptr: list[int] = [0]
    indices: list[int] = []
    weights: list[float] = []

    for i in range(n):
        wi: float = float(wind_u[i])
        wv: float = float(wind_v[i])

        if wi != 0.0 or wv != 0.0:
            row_idx: list[int] = []
            row_w: list[float] = []
            for neighbor_id in geometry.neighbors_of(cell_id=i):
                j: int = int(neighbor_id)
                d: Float64Array = torus_delta(
                    a=sites[i], b=sites[j], width=width, height=height
                )
                dist: float = float(np.hypot(d[0], d[1]))
                if dist == 0.0:
                    continue
                # Alignment of the unit offset with the wind direction.
                align: float = (float(d[0]) * wi + float(d[1]) * wv) / dist
                if align > 0.0:
                    row_idx.append(j)
                    row_w.append(align)

            total: float = sum(row_w)
            if total > 0.0:
                indices.extend(row_idx)
                weights.extend(w / total for w in row_w)

        indptr.append(len(indices))

    return (
        np.array(indptr, dtype=np.int32),
        np.array(indices, dtype=np.int32),
        np.array(weights, dtype=np.float64),
    )


def _downwind_means(
    *,
    src: Int32Array,
    indices: Int32Array,
    weights: Float64Array,
    is_sink: BoolArray,
    values: Float64Array,
) -> Float64Array:
    """Weighted mean of ``values`` over each cell's downwind neighbors.

    Computed as a scatter-add: each CSR entry contributes
    ``weight * value[target]`` back to its source cell.  Sink cells (no
    downwind edges) keep their own value, so the orographic and chill terms see
    no gradient there and contribute nothing.
    """
    n: int = values.shape[0]
    out: Float64Array = np.bincount(
        src, weights=weights * values[indices], minlength=n
    )
    out[is_sink] = values[is_sink]
    return out


def transport_moisture(
    *,
    geometry: MeshGeometry,
    downwind: tuple[Int32Array, Int32Array, Float64Array],
    temperature: Float64Array,
    elevation: Float64Array,
    is_land: BoolArray,
    cfg: MoistureConfig,
) -> Float64Array:
    """Advect ocean-sourced moisture downwind, raining it out.

    Double-buffered advection loop:
      1. Refill ocean moisture as ``evaporation × temperature``.
      2. For each cell, compute ``rainout`` from base drying, orographic
         forcing (rising into higher downwind terrain), and temperature chill
         (cooling toward the downwind cells).
      3. Accumulate rain into ``precipitation[i]``; the remainder fans out to
         the downwind neighbors by their weights.
      4. Swap buffers and repeat for ``cfg.passes`` iterations.

    After the loop, precipitation is normalized so that the
    ``cfg.wet_reference_percentile`` of *land* precipitation maps to 1.0 (land
    is what biomes read), then clipped to ``[0, 1]``.  Using a land percentile
    — rather than a global one dominated by a few drenched coastal cells —
    keeps the bulk of the land off the arid floor.

    Args:
        geometry: Torus mesh (used for cell count).
        downwind: CSR ``(indptr, indices, weights)`` from :func:`build_downwind`.
        temperature: Per-cell temperature in ``[0, 1]``.
        elevation: Per-cell elevation in ``[-1, 1]``; 0 = sea level.
        is_land: ``True`` for land cells, ``False`` for ocean.
        cfg: Moisture transport parameters.

    Returns:
        ``precipitation`` array in ``[0, 1]``.
    """
    n: int = geometry.n_cells
    indptr, indices, weights = downwind

    # Flatten the CSR for vectorized passes: ``src`` is the source cell of each
    # downwind edge; ``is_sink`` marks cells with no downwind edge.
    row_len: Int32Array = np.diff(indptr)
    src: Int32Array = np.repeat(np.arange(n, dtype=np.int32), row_len)
    is_sink: BoolArray = row_len == 0

    # Per-cell rainout is fixed across passes (wind/terrain/temperature don't
    # change), so derive its orographic and chill terms once from the
    # downwind-weighted means.
    dw_elev: Float64Array = _downwind_means(
        src=src, indices=indices, weights=weights, is_sink=is_sink, values=elevation
    )
    dw_temp: Float64Array = _downwind_means(
        src=src, indices=indices, weights=weights, is_sink=is_sink, values=temperature
    )
    uphill: Float64Array = np.maximum(0.0, dw_elev - elevation)
    chill: Float64Array = np.maximum(0.0, temperature - dw_temp)
    rainout: Float64Array = np.clip(
        cfg.base_rain + cfg.oro * uphill + cfg.chill * chill, 0.0, 1.0
    )
    # Sinks rain out everything they hold.
    rainout[is_sink] = 1.0

    moisture: Float64Array = np.zeros(shape=n, dtype=np.float64)
    precipitation: Float64Array = np.zeros(shape=n, dtype=np.float64)
    ocean_mask: BoolArray = ~is_land

    for _ in range(cfg.passes):
        # Refill ocean moisture at the start of every pass.
        moisture[ocean_mask] = cfg.evaporation * temperature[ocean_mask]

        rain: Float64Array = moisture * rainout
        precipitation += rain

        # Fan the remainder to downwind neighbors: each edge carries
        # carry[src] * weight to its target cell.
        carry: Float64Array = moisture - rain
        moisture = np.bincount(
            indices, weights=carry[src] * weights, minlength=n
        )

    # Normalize against a high percentile of *land* precipitation (the divisor
    # is near the wet maximum, so only a sliver of drenched cells clip — no
    # pile-up in the top band), then bend with a wetness gamma.  Raw rain-out
    # is heavily right-skewed (dry interiors, a wet coastal minority); a linear
    # scale alone would strand the bulk on the arid floor.  ``precip_gamma`` < 1
    # lifts the dry-to-mid range into the temperate bands without saturating the
    # wettest cells.
    land_precip: Float64Array = precipitation[is_land]
    ref: float = (
        float(np.percentile(a=land_precip, q=cfg.wet_reference_percentile))
        if land_precip.size
        else 0.0
    )
    if ref > 0.0:
        precipitation = precipitation / ref
    precipitation = np.clip(precipitation, a_min=0.0, a_max=1.0)

    if cfg.precip_gamma != 1.0:
        precipitation = precipitation**cfg.precip_gamma

    return precipitation
