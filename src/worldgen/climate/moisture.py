"""Geography-driven precipitation — a climate normal.

precip = belt(latitude) x continentality(coast_distance, sst) x orographic(wind,
relief) x (1 + perturb * convergence), composed multiplicatively and
absolute-calibrated (no floor, no relative anchor).  See
``docs/worldgen-precipitation-redesign-plan.md``.

This replaces the old iterative moisture advection, which fanned ocean moisture
downwind and rained it out: that model flooded the continent to a near-uniform
saturation (``corr(coast_distance, precip) = 0``) and needed a precipitation
floor to avoid all-desert interiors.  Here dryness emerges from geography — deep
interiors (continentality), subtropics/poles (belt), rain shadows (orographic),
and cold-current coasts (sst) — so no floor is required.
"""

from collections import deque

import numpy as np

from src.worldgen.climate.transport import aligned_edges
from src.worldgen.config.worldgen_config import MoistureConfig
from src.worldgen.geometry.field_ops import diffuse
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.workspace import Workspace
from src.worldgen.types import BoolArray, Float64Array


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


def coastal_sst_source(
    *,
    geometry: MeshGeometry,
    sst: Float64Array,
    is_land: BoolArray,
    cfg: MoistureConfig,
) -> Float64Array:
    """Ocean-temperature moisture-source strength per cell, in ``[sst_source_min, 1]``.

    Each coastal land cell seeds the field with the mean sea-surface temperature
    of its adjacent ocean cells; a multi-source BFS then carries that nearest-coast
    value inland (the same shape as ``compute_coast_distance``).  Warm coastal
    water (high sst) charges a wet source; cold currents / upwelling (low sst)
    starve the coast — the cold-current coastal deserts (Atacama, Namib).

    Args:
        geometry: Torus mesh with CSR adjacency.
        sst: Per-cell sea-surface temperature in ``[0, 1]``.
        is_land: ``True`` for land cells.
        cfg: Moisture config (``sst_source_min``, ``sst_source_gamma``).

    Returns:
        Per-cell source strength in ``[sst_source_min, 1]``.
    """
    n: int = geometry.n_cells
    is_ocean: BoolArray = ~is_land
    source: Float64Array = np.zeros(shape=n, dtype=np.float64)
    seeded: BoolArray = np.zeros(shape=n, dtype=bool)
    queue: deque[int] = deque()

    cell_id: int
    for cell_id in range(n):
        if not is_land[cell_id]:
            continue
        ocean_sst: list[float] = []
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if is_ocean[neighbor_id]:
                ocean_sst.append(float(sst[neighbor_id]))
        if ocean_sst:
            source[cell_id] = float(np.mean(ocean_sst))
            seeded[cell_id] = True
            queue.append(cell_id)

    while queue:
        current: int = queue.popleft()
        for neighbor_id in geometry.neighbors_of(cell_id=current):
            neighbor_id = int(neighbor_id)
            if seeded[neighbor_id] or not is_land[neighbor_id]:
                continue
            seeded[neighbor_id] = True
            source[neighbor_id] = source[current]
            queue.append(neighbor_id)

    # Ocean cells (and any land with no reachable coast) keep their own sst.
    source[is_ocean] = sst[is_ocean]

    clamped: Float64Array = np.clip(source, 0.0, 1.0) ** cfg.sst_source_gamma
    return cfg.sst_source_min + (1.0 - cfg.sst_source_min) * clamped


def continentality(
    *,
    geometry: MeshGeometry,
    coast_distance: Float64Array,
    sst_source: Float64Array,
    cfg: MoistureConfig,
) -> Float64Array:
    """Moisture supply: coastal source strength decaying inland from the coast.

    ``sst_source * exp(-coast_distance / reach)`` — wet near the coast (scaled by
    how warm that coast's water is), drying exponentially into the interior.  The
    wind asymmetry (which coast is wetter) is the orographic term's job, so this
    term is deliberately isotropic.

    ``coast_distance`` is in mesh *hops*, whose physical length shrinks as the mesh
    densifies, so the reach is converted from physical map units to hops via the
    cell spacing (``hops_per_unit = sqrt(n_cells) / width``).  This keeps the
    continentality gradient the same regardless of ``cell_count`` (a world at the
    coarse test mesh and at the dense gameplay mesh dry their interiors alike).

    Args:
        geometry: Torus mesh (for the hop↔distance conversion).
        coast_distance: Per-cell hops from the coast (0 at coast and ocean).
        sst_source: Per-cell coastal source strength (see ``coastal_sst_source``).
        cfg: Moisture config (``continentality_reach``, in map-width units).

    Returns:
        Per-cell moisture supply in ``[0, 1]``.
    """
    hops_per_unit: float = float(np.sqrt(geometry.n_cells)) / geometry.width
    reach_hops: float = max(cfg.continentality_reach * hops_per_unit, 1e-6)
    return sst_source * np.exp(-coast_distance / reach_hops)


def _best_upwind(
    *,
    geometry: MeshGeometry,
    wind_u: Float64Array,
    wind_v: Float64Array,
) -> Int32Array:
    """Per-cell neighbour the air arrived from (best-aligned with the upwind dir).

    Reuses ``aligned_edges`` with the *negated* wind to weight each edge by how
    well it points upwind; the highest-aligned neighbour per cell is the step the
    orographic walk follows.  Calm cells (no upwind edge) point at themselves, so
    the walk stalls and contributes no orographic effect.
    """
    n: int = geometry.n_cells
    src: Int32Array
    dst: Int32Array
    align: Float64Array
    src, dst, align = aligned_edges(geometry=geometry, wind_u=-wind_u, wind_v=-wind_v)

    best: Int32Array = np.arange(n, dtype=np.int32)
    if src.size:
        # Sort edges by (src, align); writing dst in that order lets the highest
        # alignment per source win (it is written last).
        order: Int32Array = np.lexsort((align, src))
        best[src[order]] = dst[order]
    return best


def orographic(
    *,
    geometry: MeshGeometry,
    elevation: Float64Array,
    wind_u: Float64Array,
    wind_v: Float64Array,
    cfg: MoistureConfig,
) -> Float64Array:
    """Windward-wet / leeward-dry multiplier with *extended* rain shadows.

    For each cell, walk ``orographic_lookahead`` steps upwind and record the
    tallest barrier crossed: a high upwind barrier means the air already dropped
    its moisture climbing it, so the cell sits in an extended rain shadow.
    Independently, air rising into the cell from a lower upwind neighbour
    (windward upslope) earns a wet bonus.  Bounded to ``[orographic_min,
    orographic_max]``.

    Args:
        geometry: Torus mesh with CSR adjacency.
        elevation: Per-cell elevation in ``[-1, 1]``.
        wind_u: Unit wind direction x-component.
        wind_v: Unit wind direction y-component.
        cfg: Moisture config (lookahead, shadow/windward strengths, bounds).

    Returns:
        Per-cell orographic multiplier in ``[orographic_min, orographic_max]``.
    """
    n: int = geometry.n_cells
    best_up: Int32Array = _best_upwind(
        geometry=geometry, wind_u=wind_u, wind_v=wind_v
    )

    # Windward bonus: cell higher than the air's immediate upwind origin = rising.
    upslope: Float64Array = np.maximum(0.0, elevation - elevation[best_up])
    windward: Float64Array = 1.0 + cfg.windward_gain * upslope

    # Extended shadow: tallest barrier crossed walking upwind.
    current: Int32Array = np.arange(n, dtype=np.int32)
    max_barrier: Float64Array = elevation.copy()
    _step: int
    for _step in range(cfg.orographic_lookahead):
        current = best_up[current]
        max_barrier = np.maximum(max_barrier, elevation[current])
    shadow_drop: Float64Array = np.maximum(0.0, max_barrier - elevation)
    shadow: Float64Array = np.exp(-cfg.shadow_strength * shadow_drop)

    return np.clip(windward * shadow, cfg.orographic_min, cfg.orographic_max)


def compute_precipitation(
    *,
    geometry: MeshGeometry,
    latitude: Float64Array,
    coast_distance: Float64Array,
    sst: Float64Array,
    elevation: Float64Array,
    is_land: BoolArray,
    wind_u: Float64Array,
    wind_v: Float64Array,
    convergence: Float64Array,
    cfg: MoistureConfig,
) -> Float64Array:
    """Compose the geography-driven precipitation climate normal in ``[0, 1]``.

    Multiplicative composition (any single dry factor gates the cell): the latitude
    belt sets the planetary bands, continentality x ocean source set wet coasts /
    dry interiors / cold-current deserts, orographic adds windward rain and
    leeward shadows, and the smoothed convergence field perturbs it.  Absolute —
    clipped to ``[0, 1]`` with an optional gamma, no floor and no relative anchor,
    so worlds keep their individual wet/dry character.

    Returns:
        ``precipitation`` array in ``[0, 1]``.
    """
    belt: Float64Array = precip_belt(latitude=latitude, cfg=cfg)
    belt = cfg.belt_floor + (1.0 - cfg.belt_floor) * belt

    source: Float64Array = coastal_sst_source(
        geometry=geometry, sst=sst, is_land=is_land, cfg=cfg
    )
    supply: Float64Array = continentality(
        geometry=geometry, coast_distance=coast_distance, sst_source=source, cfg=cfg
    )
    oro: Float64Array = orographic(
        geometry=geometry,
        elevation=elevation,
        wind_u=wind_u,
        wind_v=wind_v,
        cfg=cfg,
    )
    perturb: Float64Array = 1.0 + cfg.convergence_perturb * convergence

    precip: Float64Array = belt * supply * oro * perturb
    if cfg.precip_gamma != 1.0:
        precip = np.clip(precip, a_min=0.0, a_max=None) ** cfg.precip_gamma
    precip = np.clip(precip, a_min=0.0, a_max=1.0)

    # A light pass cleans directed-walk artifacts on the irregular mesh; the field
    # is otherwise smooth by construction (this is a climate normal, not weather).
    if cfg.smoothing_passes > 0 and cfg.smoothing_strength > 0.0:
        precip = diffuse(
            geometry=geometry,
            field=precip,
            strength=cfg.smoothing_strength,
            passes=cfg.smoothing_passes,
        )
    return precip


class MoistureStage:
    """Geography-driven precipitation (a climate normal).

    Pipeline order: ``Insolation -> Wind -> OceanCurrent -> Temperature ->
    Moisture``.  Precipitation composes the latitude belt, continentality (coast
    distance) scaled by the wind-advected ``sst`` ocean source, orographic rain
    shadows, and a convergence perturbation — no iterative advection.  See
    ``docs/worldgen-precipitation-redesign-plan.md``.
    """

    reads: tuple[str, ...] = ("coast_distance", "convergence", "elevation", "is_land", "latitude", "sst", "wind_u", "wind_v")
    writes: tuple[str, ...] = ("precipitation",)

    def run(self, ctx: Workspace) -> None:
        """Compute precipitation and write ``ctx.fields.precipitation``."""
        cfg: MoistureConfig = ctx.config.moisture

        # --- prerequisites ---
        latitude_field: Float64Array = ctx.fields.latitude

        coast_distance_field: Float64Array = ctx.fields.coast_distance

        sst_field: Float64Array = ctx.fields.sst

        elevation_field: Float64Array = ctx.fields.elevation

        is_land_field: BoolArray = ctx.fields.is_land

        wind_u_field: Float64Array = ctx.fields.wind_u

        wind_v_field: Float64Array = ctx.fields.wind_v

        convergence_field: Float64Array = ctx.fields.convergence

        ctx.fields.precipitation = compute_precipitation(
            geometry=ctx.geometry,
            latitude=latitude_field,
            coast_distance=coast_distance_field,
            sst=sst_field,
            elevation=elevation_field,
            is_land=is_land_field,
            wind_u=wind_u_field,
            wind_v=wind_v_field,
            convergence=convergence_field,
            cfg=cfg,
        )
