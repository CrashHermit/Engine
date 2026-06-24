import numpy as np

from src.worldgen.climate.transport import aligned_edges, normalize_per_source
from src.worldgen.config.worldgen_config import MoistureConfig
from src.worldgen.geometry.mesh import MeshGeometry
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
    n: int = geometry.n_cells
    src: Int32Array
    indices: Int32Array
    align: Float64Array
    src, indices, align = aligned_edges(
        geometry=geometry, wind_u=wind_u, wind_v=wind_v
    )
    indptr: Int32Array
    weights: Float64Array
    indptr, weights = normalize_per_source(src=src, align=align, n=n)
    return indptr, indices, weights


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


def precip_belt(*, latitude: Float64Array, cfg: MoistureConfig) -> Float64Array:
    """Latitudinal precipitation baseline in [0, 1] from Hadley structure.

    Two Gaussian wet bumps in ``|latitude|`` — the equatorial ITCZ at 0 and the
    temperate belt near ``belt_temperate_center`` — with the dry subtropical
    "horse latitudes" emerging as the gap between them and the dry poles as the
    falloff past the temperate bump.  Normalized so the equatorial peak is ~1.

    Args:
        latitude: Signed latitude in ``[-1, 1]`` (0 equator, +/-1 poles).
        cfg: Moisture config (belt weights, centers, widths).

    Returns:
        Per-cell baseline precipitation in ``[0, 1]``.
    """
    lat_abs: Float64Array = np.abs(latitude)
    equator: Float64Array = cfg.belt_equator_weight * np.exp(
        -((lat_abs / cfg.belt_equator_sigma) ** 2)
    )
    temperate: Float64Array = cfg.belt_temperate_weight * np.exp(
        -(((lat_abs - cfg.belt_temperate_center) / cfg.belt_temperate_sigma) ** 2)
    )
    belt: Float64Array = (equator + temperate) / max(cfg.belt_equator_weight, 1e-9)
    return np.clip(belt, 0.0, 1.0)


def transport_moisture(
    *,
    geometry: MeshGeometry,
    downwind: tuple[Int32Array, Int32Array, Float64Array],
    temperature: Float64Array,
    sst: Float64Array,
    elevation: Float64Array,
    is_land: BoolArray,
    latitude: Float64Array,
    convergence: Float64Array,
    cfg: MoistureConfig,
) -> Float64Array:
    """Advect ocean-sourced moisture downwind, raining it out.

    Double-buffered advection loop:
      1. Refill ocean moisture as ``evaporation × sst`` (Clausius-Clapeyron:
         warm water charges the air with more vapor, so warm currents feed wet
         downwind coasts and cold currents starve them).
      2. For each cell, compute ``rainout`` from base drying, orographic
         forcing (rising into higher downwind terrain), and temperature chill
         (cooling toward the downwind cells).
      3. Accumulate rain into ``precipitation[i]``; the remainder fans out to
         the downwind neighbors by their weights.
      4. Swap buffers and repeat for ``cfg.passes`` iterations.

    After the loop, precipitation is normalized with a smooth saturating curve
    ``p = raw / (raw + k)``, where ``k`` is the ``cfg.wet_anchor_percentile`` of
    *land* rain-out (land is what biomes read).  The anchor maps to 0.5, the dry
    interior stays dry, and the heavy wet tail compresses smoothly toward 1 — so
    neither the arid floor nor the wet ceiling piles up the way a
    percentile-and-clip scale did.

    Args:
        geometry: Torus mesh (used for cell count).
        downwind: CSR ``(indptr, indices, weights)`` from :func:`build_downwind`.
        temperature: Per-cell temperature in ``[0, 1]`` (drives the chill term).
        sst: Per-cell sea-surface temperature in ``[0, 1]`` (drives ocean
            evaporation; warm currents evaporate more).
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
    # Convergence (rising air) rains moisture out alongside orographic and chill
    # uplift — the term that makes the latitudinal banding emerge from the wind
    # field instead of an authored belt.
    rainout: Float64Array = np.clip(
        cfg.base_rain
        + cfg.oro * uphill
        + cfg.chill * chill
        + cfg.convergence_weight * convergence,
        0.0,
        1.0,
    )
    # Sinks rain out everything they hold.
    rainout[is_sink] = 1.0

    moisture: Float64Array = np.zeros(shape=n, dtype=np.float64)
    precipitation: Float64Array = np.zeros(shape=n, dtype=np.float64)
    ocean_mask: BoolArray = ~is_land

    for _ in range(cfg.passes):
        # Refill ocean moisture at the start of every pass (evaporation ∝ SST).
        moisture[ocean_mask] = cfg.evaporation * sst[ocean_mask]

        rain: Float64Array = moisture * rainout
        precipitation += rain

        # Fan the remainder to downwind neighbors: each edge carries
        # carry[src] * weight to its target cell.
        carry: Float64Array = moisture - rain
        moisture = np.bincount(
            indices, weights=carry[src] * weights, minlength=n
        )

    # Saturating normalization: ``p = raw / (raw + k)``, ``k`` = a land-rain-out
    # percentile.  The anchor maps to 0.5; the dry interior stays dry and the
    # heavy wet tail compresses smoothly toward 1, so neither the arid floor nor
    # the wet ceiling piles up (a percentile-and-clip scale did one or the
    # other).  Computed on *land* so a few drenched coastal cells don't set it.
    land_precip: Float64Array = precipitation[is_land]
    anchor: float = (
        float(np.percentile(a=land_precip, q=cfg.wet_anchor_percentile))
        if land_precip.size
        else 0.0
    )
    if anchor > 0.0:
        precipitation = precipitation / (precipitation + anchor)
    advected: Float64Array = np.clip(precipitation, a_min=0.0, a_max=1.0)

    # --- latitude rain belts (primary) modulated by advection (local detail) ---
    # ``precip = belt * (adv_floor + (1 - adv_floor) * advected)``: the belt sets
    # the wet/dry banding (wet ITCZ, dry subtropics, wet temperate, dry poles),
    # and advection lifts a cell from ``adv_floor`` of its baseline (deep, dry
    # interior — but the ITCZ still rains) up to the full baseline (wet windward
    # coast).  Multiplicative, so a dry belt OR a rain shadow both dry a cell:
    # subtropical coasts stay desert, temperate lee stays dry.
    # ``belt_trim`` blends the authored belt toward 1.0 (no banding of its own),
    # ceding the latitudinal banding to the convergence rainout above.
    belt: Float64Array = precip_belt(latitude=latitude, cfg=cfg)
    belt = belt + cfg.belt_trim * (1.0 - belt)
    modulation: Float64Array = cfg.belt_adv_floor + (
        1.0 - cfg.belt_adv_floor
    ) * advected
    precipitation = np.clip(belt * modulation, a_min=0.0, a_max=1.0)

    if cfg.precip_gamma != 1.0:
        precipitation = precipitation**cfg.precip_gamma

    return precipitation
