"""Lake extraction with outlet finding.

Phase 3 step 4: lakes as connected components of water-filled depressions.

A lake is a connected blob of cells where ``z_filled > z + epsilon``
(terrain below the spill surface).  Its surface is the shared ``z_filled``
value, and its outlet is the spill cell where water would overflow — the
boundary cell whose outside neighbor has the lowest ``z_filled``.

``z_filled`` is the bias-free priority-flood surface, *not* the routing
surface ``z_route``: the latter's ``eps * hops`` flat-draining bias would
masquerade as lake depth and drown large worlds in phantom lakes.
"""

from collections import deque

import numpy as np

from src.core.model.environment.water.lake import Lake
from src.worldgen.config.worldgen_config import LakeConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.workspace import Workspace
from src.core.model.environment.terrain.volcano import Volcano


def components(
    *,
    geometry: MeshGeometry,
    mask: BoolArray,
) -> Int32Array:
    """Label connected components of ``mask`` via BFS over CSR adjacency.

    This is the one connected-components idiom in the codebase, factored out
    of ``terrain/finalize.py::label_landmasses`` so the water layer reuses the
    exact BFS shape (``deque`` queue, the label array doubles as the visited
    mask, ``int(neighbor_id)`` conversion).  Cells outside ``mask`` get ``-1``;
    in-mask cells get a 0-based component id.

    Args:
        geometry: Torus mesh with CSR adjacency.
        mask: Boolean mask selecting the cells to label.

    Returns:
        labels: Per-cell 0-based component id; ``-1`` for cells outside
            the mask.
    """
    n: int = len(mask)
    labels: Int32Array = np.full(n, -1, dtype=np.int32)
    component_id: int = -1

    cell_id: int
    for cell_id in range(n):
        if not mask[cell_id] or labels[cell_id] >= 0:
            continue

        component_id += 1

        # BFS from this unvisited masked cell.
        queue: deque[int] = deque()
        queue.append(cell_id)
        labels[cell_id] = component_id

        while queue:
            current: int = queue.popleft()
            for neighbor_id in geometry.neighbors_of(cell_id=current):
                neighbor_id = int(neighbor_id)
                if labels[neighbor_id] >= 0 or not mask[neighbor_id]:
                    continue
                labels[neighbor_id] = component_id
                queue.append(neighbor_id)

    return labels


def extract_lakes(
    *,
    geometry: MeshGeometry,
    z: Float64Array,
    z_filled: Float64Array,
    is_land: BoolArray,
    discharge: Float64Array,
    evaporation: Float64Array,
    cfg: LakeConfig,
) -> tuple[list[Lake], Int32Array, BoolArray]:
    """Extract water-balanced lakes from terrain depressions.

    Geometry alone tells us where water *could* pool (a depression is a
    connected blob of cells where ``z_filled > z + epsilon`` — the bias-free
    spill surface rising above terrain).  But a depression only *holds* a lake
    if its catchment delivers enough water to offset surface evaporation, so
    each depression is filled by a water balance rather than flooded to its
    brim unconditionally:

    - **Inflow** ``Q_in`` is the catchment rainfall reaching the basin: the
      maximum ``discharge`` over its cells (all basin cells drain to the pit,
      whose discharge is the accumulated upstream precipitation).
    - **Loss** at water level ``h`` is the surface evaporation of the submerged
      cells, ``sum(evaporation[c] for c in basin if z[c] < h)``.
    - The lake fills to the level where loss equals inflow.  Sort the basin
      cells by elevation and submerge the lowest ones until their cumulative
      evaporation reaches ``Q_in``.  If even the full pool (up to the spill)
      evaporates less than ``Q_in``, the lake brims over its spill and is
      **exorheic** (overflow continues downstream).  Otherwise it equilibrates
      at a partial level below the spill and is **endorheic** (all inflow
      evaporates; arid basins may submerge nothing at all — a salt flat).

    ``z_filled`` (not the routing surface ``z_route``) defines the depressions:
    ``z_route``'s ``eps * hops`` flat-draining bias accumulates with path length
    and, at large world sizes, would lift vast non-bowl regions a hair above
    ``z`` and drown the map in phantom lakes.

    Args:
        geometry: Torus mesh with CSR adjacency.
        z: Per-cell terrain elevation.
        z_filled: Per-cell physical spill surface (bias-free priority-flood).
        is_land: Boolean mask identifying land cells.
        discharge: Per-cell accumulated upstream precipitation (inflow source).
        evaporation: Per-cell potential evaporation, in the same units as
            ``discharge`` (precipitation-equivalent), summed over submerged
            cells as the loss term.
        cfg: Lake configuration (``epsilon`` candidate-depth floor).

    Returns:
        lakes: List of water-balanced ``Lake`` objects (0-based ids).
        lake_id: Per-cell lake id (``-1`` = no lake / not submerged).
        is_lake: Boolean array marking submerged lake cells.
    """
    n: int = len(z)
    epsilon: float = cfg.epsilon
    is_lake: BoolArray = np.zeros(n, dtype=bool)
    lake_id: Int32Array = np.full(n, -1, dtype=np.int32)

    # --- 1. Candidate depressions: connected components of the geometric pool ---
    depression_mask: BoolArray = is_land & (z_filled > z + epsilon)
    component_id: Int32Array = components(geometry=geometry, mask=depression_mask)
    n_components: int = int(component_id.max()) + 1 if component_id.size else 0
    if n_components <= 0:
        return [], lake_id, is_lake

    cells_by_component: list[list[int]] = [[] for _ in range(n_components)]
    cell_id: int
    for cell_id in range(n):
        label: int = int(component_id[cell_id])
        if label >= 0:
            cells_by_component[label].append(cell_id)

    # --- 2. Water-balance each depression into a (possibly partial) lake ---
    lakes: list[Lake] = []
    next_lake_id: int = 0
    for component_cells in cells_by_component:
        submerged, level, brims = _fill_basin(
            component_cells=component_cells,
            z=z,
            z_filled=z_filled,
            discharge=discharge,
            evaporation=evaporation,
        )
        if not submerged:
            continue  # arid basin: dry / salt flat, no standing water

        inflow: float = max(float(discharge[c]) for c in component_cells)
        outlet_cell: int | None = (
            _find_outlet(
                component_cells=submerged,
                geometry=geometry,
                z_filled=z_filled,
            )
            if brims
            else None
        )

        for c in submerged:
            is_lake[c] = True
            lake_id[c] = next_lake_id

        lakes.append(
            Lake(
                id=next_lake_id,
                cells=submerged,
                surface_level=level,
                outlet_cell=outlet_cell,
                endorheic=not brims,
                inflow=inflow,
            )
        )
        next_lake_id += 1

    return lakes, lake_id, is_lake


def _fill_basin(
    *,
    component_cells: list[int],
    z: Float64Array,
    z_filled: Float64Array,
    discharge: Float64Array,
    evaporation: Float64Array,
) -> tuple[list[int], float, bool]:
    """Solve a depression's equilibrium water level from its water balance.

    Submerge the basin's lowest cells until their cumulative evaporation
    reaches the inflow; the lake brims over its spill if even the full pool
    evaporates less than the inflow.

    Args:
        component_cells: Mesh cell ids of the geometric depression.
        z: Per-cell terrain elevation.
        z_filled: Per-cell spill surface (its shared value is the spill level).
        discharge: Per-cell accumulated upstream precipitation.
        evaporation: Per-cell potential evaporation (precip-equivalent units).

    Returns:
        (submerged_cells, surface_level, brims): cells under water (lowest-first),
        the equilibrium surface elevation, and whether the lake reached its spill.
    """
    spill_level: float = float(z_filled[component_cells[0]])
    inflow: float = max(float(discharge[c]) for c in component_cells)

    # Lowest cells flood first; accumulate evaporation as the water rises.
    ordered: list[int] = sorted(component_cells, key=lambda c: float(z[c]))

    cumulative_evap: float = 0.0
    submerged: list[int] = []
    for c in ordered:
        next_evap: float = cumulative_evap + float(evaporation[c])
        if next_evap > inflow:
            # This cell would tip evaporation past inflow: water equilibrates
            # at its rim.  The lake is partial (endorheic) and stops here.
            level: float = float(z[c])
            return submerged, level, False
        cumulative_evap = next_evap
        submerged.append(c)

    # Inflow outlasts evaporation over the whole pool: fills to the spill and
    # overflows (exorheic).
    return submerged, spill_level, True


def _find_outlet(
    *,
    component_cells: list[int],
    geometry: MeshGeometry,
    z_filled: Float64Array,
) -> int | None:
    """Find the outlet cell of a lake component.

    The outlet is the boundary cell of the lake whose outside neighbor
    has the lowest ``z_filled``.  If every outside neighbor is higher
    than the lake's surface (the lake is a hydrological sink), the lake
    is terminal: returns ``None``.

    Args:
        component_cells: Mesh cell ids belonging to this lake.
        geometry: Torus mesh with CSR adjacency.
        z_filled: Per-cell physical spill surface.

    Returns:
        Outlet cell id, or ``None`` for terminal (endorheic) lakes.
    """
    lake_set: set[int] = set(component_cells)

    # Surface level: use the minimum z_filled in the lake (water is level).
    surface_level: float = min(float(z_filled[c]) for c in component_cells)

    best_outside_z: float = float("inf")
    outlet_cell: int | None = None

    for cell_id in component_cells:
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if neighbor_id in lake_set:
                continue

            outside_z: float = float(z_filled[neighbor_id])
            if outside_z < best_outside_z:
                best_outside_z = outside_z
                outlet_cell = cell_id

    # Terminal lake: all outside neighbors are higher than the lake's
    # surface — water doesn't spill, it collects.
    if best_outside_z > surface_level:
        return None

    return outlet_cell


class LakesStage:
    """Extract lakes and write is_lake / lake_id to fields.

    Phase 3 step 4: ``extract_lakes`` — BFS connected components on the
    lake mask ``is_land & (z_filled > z + epsilon)``, outlet finding, and
    ``Lake`` object construction.

    Pipeline order: after RiversStage, before Flow stage.
    """

    reads: tuple[str, ...] = (
        "elevation", "is_land", "z_filled", "discharge", "temperature",
    )
    writes: tuple[str, ...] = ("is_lake", "lake_id")

    def run(self, ctx: Workspace) -> None:
        """Extract lakes and write is_lake, lake_id, and ctx.outputs.lakes."""
        n: int = ctx.geometry.n_cells
        cfg: LakeConfig = ctx.config.lake

        # --- prerequisites ---
        z_field = ctx.fields.z_filled
        if z_field is None:
            msg: str = "z_filled must be set before LakesStage"
            raise RuntimeError(msg)
        z_filled = z_field

        elevation_field = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before LakesStage"
            raise RuntimeError(msg)
        elevation = elevation_field

        is_land_field = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before LakesStage"
            raise RuntimeError(msg)
        is_land = is_land_field

        discharge_field = ctx.fields.discharge
        if discharge_field is None:
            msg = "discharge must be set before LakesStage"
            raise RuntimeError(msg)
        discharge = discharge_field

        temperature_field = ctx.fields.temperature
        if temperature_field is None:
            msg = "temperature must be set before LakesStage"
            raise RuntimeError(msg)
        # Potential evaporation as the lake water balance's loss term, in the
        # same precipitation-equivalent units as discharge: warmer climate
        # evaporates more.  Clamp temperature to non-negative so frozen cells
        # don't subtract water.
        evaporation = cfg.evap_scale * np.maximum(temperature_field, 0.0)

        # --- Extract lakes ---
        lakes, lake_id, is_lake = extract_lakes(
            geometry=ctx.geometry,
            z=elevation,
            z_filled=z_filled,
            is_land=is_land,
            discharge=discharge,
            evaporation=evaporation,
            cfg=cfg,
        )
        # --- Inject crater lakes for land calderas (cross-stage coupling) ---
        volcanoes: list[Volcano] | None = ctx.outputs.volcanoes
        if volcanoes:
            next_id: int = len(lakes)
            for volcano in volcanoes:
                cell: int = volcano.cell
                if not volcano.has_caldera or not is_land[cell] or is_lake[cell]:
                    continue
                is_lake[cell] = True
                lake_id[cell] = next_id
                lakes.append(
                    Lake(
                        id=next_id,
                        cells=[cell],
                        surface_level=float(elevation[cell]),
                        outlet_cell=None,  # terminal crater lake
                        endorheic=True,
                    )
                )
                next_id += 1

        ctx.outputs.lakes = lakes

        # --- Write to fields ---
        ctx.fields.is_lake = is_lake
        ctx.fields.lake_id = lake_id
