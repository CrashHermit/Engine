"""Lake extraction with outlet finding.

Phase 3 step 4: lakes as connected components of water-filled depressions.

A lake is a connected blob of cells where ``z_route > z + epsilon``
(terrain below the water surface).  Its surface is the shared ``z_route``
value, and its outlet is the spill cell where water would overflow — the
boundary cell whose outside neighbor has the lowest ``z_route``.
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
    z_route: Float64Array,
    is_land: BoolArray,
    cfg: LakeConfig,
) -> tuple[list[Lake], Int32Array, BoolArray]:
    """Extract lakes as connected components of water-filled depressions.

    A lake is a connected blob of cells where ``z_route > z + epsilon``,
    its surface is their shared ``z_route`` value, and its outlet is the
    spill cell where water would overflow.

    The lake mask is ``is_land & (z_route > z + epsilon)`` — the epsilon
    avoids labeling numerically-flat-but-not-bowl cells as lakes.

    **Outlet finding:** the boundary cell of the lake whose outside neighbor
    has the lowest ``z_route`` — that's where the flood spilled in, and
    therefore where water spills out.  If every outside neighbor is higher,
    the lake is terminal: ``outlet_cell = None``.

    Args:
        geometry: Torus mesh with CSR adjacency.
        z: Per-cell terrain elevation (for mask computation).
        z_route: Per-cell water-surface elevation from priority-flood.
        is_land: Boolean mask identifying land cells.
        cfg: Lake configuration with ``epsilon`` (minimum depth threshold).

    Returns:
        lakes: List of ``Lake`` objects (0-based ids).
        lake_id: Per-cell lake id (``-1`` = no lake).
        is_lake: Boolean array marking lake cells.
    """
    n: int = len(z)
    epsilon: float = cfg.epsilon

    # --- 1. Lake mask ---
    lake_mask: BoolArray = is_land & (z_route > z + epsilon)
    is_lake: BoolArray = lake_mask

    # --- 2. Connected components via the shared BFS helper ---
    lake_id: Int32Array = components(geometry=geometry, mask=lake_mask)
    n_lakes: int = int(lake_id.max()) + 1 if lake_id.size else 0
    if n_lakes <= 0:
        return [], lake_id, is_lake

    # Group cell ids by component label in a single pass.
    cells_by_lake: list[list[int]] = [[] for _ in range(n_lakes)]
    cell_id: int
    for cell_id in range(n):
        label: int = int(lake_id[cell_id])
        if label >= 0:
            cells_by_lake[label].append(cell_id)

    # --- 3. Build Lake objects and find outlets ---
    lakes: list[Lake] = []
    lake_idx: int
    component_cells: list[int]
    for lake_idx, component_cells in enumerate(cells_by_lake):
        # A filled lake shares one z_route surface; any member reports it.
        surface_level: float = float(z_route[component_cells[0]])

        outlet_cell: int | None = _find_outlet(
            component_cells=component_cells,
            geometry=geometry,
            z_route=z_route,
        )

        lakes.append(
            Lake(
                id=lake_idx,
                cells=component_cells,
                surface_level=surface_level,
                outlet_cell=outlet_cell,
            )
        )

    return lakes, lake_id, is_lake


def _find_outlet(
    *,
    component_cells: list[int],
    geometry: MeshGeometry,
    z_route: Float64Array,
) -> int | None:
    """Find the outlet cell of a lake component.

    The outlet is the boundary cell of the lake whose outside neighbor
    has the lowest ``z_route``.  If every outside neighbor is higher
    than the lake's surface (the lake is a hydrological sink), the lake
    is terminal: returns ``None``.

    Args:
        component_cells: Mesh cell ids belonging to this lake.
        geometry: Torus mesh with CSR adjacency.
        z_route: Per-cell water-surface elevation.

    Returns:
        Outlet cell id, or ``None`` for terminal (endorheic) lakes.
    """
    lake_set: set[int] = set(component_cells)

    # Surface level: use the minimum z_route in the lake (water is level).
    surface_level: float = min(float(z_route[c]) for c in component_cells)

    best_outside_z: float = float("inf")
    outlet_cell: int | None = None

    for cell_id in component_cells:
        for neighbor_id in geometry.neighbors_of(cell_id=cell_id):
            neighbor_id = int(neighbor_id)
            if neighbor_id in lake_set:
                continue

            outside_z: float = float(z_route[neighbor_id])
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
    lake mask ``is_land & (z_route > z + epsilon)``, outlet finding, and
    ``Lake`` object construction.

    Pipeline order: after RiversStage, before Flow stage.
    """

    reads: tuple[str, ...] = ("elevation", "is_land", "z_route")
    writes: tuple[str, ...] = ("is_lake", "lake_id")

    def run(self, ctx: Workspace) -> None:
        """Extract lakes and write is_lake, lake_id, and ctx.outputs.lakes."""
        n: int = ctx.geometry.n_cells
        cfg: LakeConfig = ctx.config.lake

        # --- prerequisites ---
        z_field = ctx.fields.z_route
        if z_field is None:
            msg: str = "z_route must be set before LakesStage"
            raise RuntimeError(msg)
        z_route = z_field

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

        # --- Extract lakes ---
        lakes, lake_id, is_lake = extract_lakes(
            geometry=ctx.geometry,
            z=elevation,
            z_route=z_route,
            is_land=is_land,
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
                    )
                )
                next_id += 1

        ctx.outputs.lakes = lakes

        # --- Write to fields ---
        ctx.fields.is_lake = is_lake
        ctx.fields.lake_id = lake_id
