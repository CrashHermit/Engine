"""Wind-advected sea-surface temperature — toroidal ocean currents.

Heat is seeded from the ocean's latitude baseline (``insolation``), advected
along the prevailing wind, and relaxed back toward that baseline at the air-sea
thermal relaxation rate.  Two geometry facts do all the "current" work, with no
faked Coriolis:

* **Ocean-only transport.** Heat moves over ocean->ocean edges only, so land is
  a barrier.  A current that meets a coast can only continue through the ocean
  cells *along* the shore, so it deflects and runs down the coastline —
  continent-deflected gyres and the warm-coast/cold-coast pair emerge for free.
  Enclosed seas become isolated thermal basins.
* **No-normal-flow boundary condition.** Where the wind would drive water into
  land, the flow direction is projected onto the coastline tangent (mass
  conservation: water cannot flow into the shore), so currents hug coasts
  instead of piling up and stopping at the point of impact.

On a torus the x-axis wraps, so an all-ocean latitude band is an unbroken
*circumpolar* current that homogenizes temperature all the way around — the
signature toroidal effect.

See ``docs/worldgen-ocean-currents-plan.md``.
"""

import numpy as np

from src.worldgen.climate.transport import (
    aligned_edges,
    normalize_per_receiver,
)
from src.worldgen.config.worldgen_config import OceanCurrentConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.context import WorldContext
from src.worldgen.types import BoolArray, Float64Array


def _coast_projected_wind(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
    is_land: BoolArray,
) -> tuple[Float64Array, Float64Array]:
    """Project each ocean cell's wind onto the coastline tangent (no-normal-flow).

    The coast normal at an ocean cell is the mean unit offset toward its land
    neighbors (points from ocean into land).  Any wind component blowing *into*
    land is removed, leaving along-shore (tangent) flow; interior ocean cells
    (no land neighbor) are untouched.  Returns unit directions; a cell whose
    wind blows straight into a concave corner becomes zero (a transport sink).
    """
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = geometry.n_cells

    eff_u: Float64Array = wind_u.copy()
    eff_v: Float64Array = wind_v.copy()

    for i in range(n):
        if is_land[i]:
            continue
        nx: float = 0.0
        ny: float = 0.0
        for neighbor_id in geometry.neighbors_of(cell_id=i):
            j: int = int(neighbor_id)
            if not is_land[j]:
                continue
            d: Float64Array = torus_delta(
                a=sites[i], b=sites[j], width=width, height=height
            )
            dist: float = float(np.hypot(d[0], d[1]))
            if dist == 0.0:
                continue
            nx += float(d[0]) / dist
            ny += float(d[1]) / dist

        nmag: float = float(np.hypot(nx, ny))
        if nmag == 0.0:
            continue  # interior ocean: wind unchanged
        nx /= nmag
        ny /= nmag

        into_land: float = float(wind_u[i]) * nx + float(wind_v[i]) * ny
        if into_land <= 0.0:
            continue  # wind already blows offshore / along-shore
        eu: float = float(wind_u[i]) - into_land * nx
        ev: float = float(wind_v[i]) - into_land * ny
        emag: float = float(np.hypot(eu, ev))
        if emag > 0.0:
            eff_u[i] = eu / emag
            eff_v[i] = ev / emag
        else:
            eff_u[i] = 0.0
            eff_v[i] = 0.0

    return eff_u, eff_v


def _build_upwind_gather(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
    participates: BoolArray,
) -> tuple[Int32Array, Int32Array, Float64Array]:
    """Per-cell upwind gather over edges where both endpoints participate.

    A cell takes the temperature of the water/air flowing *into* it, so each
    wind-aligned edge (shared :func:`aligned_edges`) is normalized to sum to one
    per *receiver* — the weighted mean of the cells flowing into it.

    Returns ``(src, dst, weight)`` flat edge arrays: edge ``k`` carries
    ``weight[k] * value[src[k]]`` into ``dst[k]``.  Cells that never appear in
    ``dst`` have no upwind source (they are flow origins / sinks).
    """
    n: int = geometry.n_cells
    src: Int32Array
    dst: Int32Array
    align: Float64Array
    src, dst, align = aligned_edges(
        geometry=geometry,
        wind_u=wind_u,
        wind_v=wind_v,
        participates=participates,
    )
    weight: Float64Array = normalize_per_receiver(dst=dst, align=align, n=n)
    return src, dst, weight


def compute_sst(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
    insolation: Float64Array,
    is_land: BoolArray,
    cfg: OceanCurrentConfig,
) -> Float64Array:
    """Sea-surface temperature in [0, 1]: wind-advected current + relaxation.

    Ocean cells carry heat downwind (gathering their upwind neighbors' SST) and
    relax toward the latitude baseline each pass; land cells carry their own
    radiative baseline (there is no sea there).  Bounded by construction (a
    convex blend of baseline and upwind values), so no cell ever exceeds its
    warmest source — no runaway.

    Args:
        geometry: Torus mesh with CSR adjacency.
        wind_u: Unit prevailing-wind x-component (shape ``(n_cells,)``).
        wind_v: Unit prevailing-wind y-component.
        insolation: Latitude-derived radiative baseline in ``[0, 1]``.
        is_land: ``True`` for land cells, ``False`` for ocean.
        cfg: Ocean-current parameters (passes, relaxation rate).

    Returns:
        Per-cell ``sst`` in ``[0, 1]``.
    """
    n: int = geometry.n_cells
    baseline: Float64Array = np.clip(insolation, 0.0, 1.0)
    ocean: BoolArray = ~is_land

    # No-normal-flow boundary condition, then the ocean-only upwind gather.
    eff_u, eff_v = _coast_projected_wind(
        geometry=geometry, wind_u=wind_u, wind_v=wind_v, is_land=is_land
    )
    src, dst, weight = _build_upwind_gather(
        geometry=geometry, wind_u=eff_u, wind_v=eff_v, participates=ocean
    )

    # An ocean cell with no upwind ocean source is a flow origin: it holds its
    # own baseline (the relaxation target), so warmth/cold is *injected* there.
    has_source: BoolArray = np.zeros(n, dtype=bool)
    if dst.size:
        has_source[np.unique(dst)] = True
    update: BoolArray = ocean & has_source

    relax: float = cfg.relaxation
    sst: Float64Array = baseline.copy()
    for _ in range(cfg.passes):
        gathered: Float64Array = (
            np.asarray(
                np.bincount(dst, weights=weight * sst[src], minlength=n),
                dtype=np.float64,
            )
            if dst.size
            else np.zeros(n, dtype=np.float64)
        )
        new: Float64Array = sst.copy()
        new[update] = relax * baseline[update] + (1.0 - relax) * gathered[update]
        sst = new

    # Land carries its own radiative baseline; ocean sinks already equal it.
    sst[is_land] = baseline[is_land]
    return np.clip(sst, 0.0, 1.0)


def maritime_sst_onshore(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
    sst: Float64Array,
    insolation: Float64Array,
    is_land: BoolArray,
    reach: float,
) -> Float64Array:
    """Carry ocean SST inland along the wind for the maritime-moderation term.

    Maritime *air* crosses coasts freely (unlike the water), so this uses the
    raw wind over the full mesh: ocean cells are fixed sources at their SST, and
    each land cell takes the SST of the water the wind brought onshore (the
    upwind average).  The inland *decay* of the effect is handled downstream by
    the temperature stage's ``exp(-coast_distance / reach)`` weight, so here we
    just propagate the value ~``reach`` hops inland.

    Returns a per-cell field equal to ``sst`` on ocean and the wind-borne ocean
    SST on land (land cells with no upwind source keep their own baseline).
    """
    n: int = geometry.n_cells
    participates: BoolArray = np.ones(n, dtype=bool)
    src, dst, weight = _build_upwind_gather(
        geometry=geometry, wind_u=wind_u, wind_v=wind_v, participates=participates
    )

    has_source: BoolArray = np.zeros(n, dtype=bool)
    if dst.size:
        has_source[np.unique(dst)] = True
    update: BoolArray = is_land & has_source

    maritime: Float64Array = np.where(is_land, insolation, sst).astype(np.float64)
    passes: int = max(1, int(round(3.0 * reach)))
    for _ in range(passes):
        gathered: Float64Array = (
            np.asarray(
                np.bincount(dst, weights=weight * maritime[src], minlength=n),
                dtype=np.float64,
            )
            if dst.size
            else np.zeros(n, dtype=np.float64)
        )
        maritime[update] = gathered[update]
        maritime[~is_land] = sst[~is_land]  # ocean stays a fixed source

    return np.clip(maritime, 0.0, 1.0)


class OceanCurrentStage:
    """Compute wind-advected sea-surface temperature (toroidal currents).

    Pipeline order: ``Insolation → Wind → OceanCurrent → Temperature → Moisture``.
    Writes ``ctx.fields.sst``, which Temperature (maritime moderation) and
    Moisture (evaporation) then consume.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute SST and write ``ctx.fields.sst``."""
        cfg: OceanCurrentConfig = ctx.config.ocean_current

        # --- prerequisites ---
        insolation_field: Float64Array | None = ctx.fields.insolation
        if insolation_field is None:
            msg: str = "insolation must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        insolation: Float64Array = insolation_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg = "is_land must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        wind_u_field: Float64Array | None = ctx.fields.wind_u
        if wind_u_field is None:
            msg = "wind_u must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        wind_u: Float64Array = wind_u_field

        wind_v_field: Float64Array | None = ctx.fields.wind_v
        if wind_v_field is None:
            msg = "wind_v must be set before OceanCurrentStage"
            raise RuntimeError(msg)
        wind_v: Float64Array = wind_v_field

        # --- compute ---
        ctx.fields.sst = compute_sst(
            geometry=ctx.geometry,
            wind_u=wind_u,
            wind_v=wind_v,
            insolation=insolation,
            is_land=is_land,
            cfg=cfg,
        )
