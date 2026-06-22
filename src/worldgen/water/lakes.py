"""Lake extraction with outlet finding.

Phase 3 step 4: lakes as connected components of water-filled depressions.

A lake is a connected blob of cells where ``z_route > z + epsilon``
(terrain below the water surface).  Its surface is the shared ``z_route``
value, and its outlet is the spill cell where water would overflow — the
boundary cell whose outside neighbor has the lowest ``z_route``.
"""

from collections import deque

import numpy as np

from src.worldgen.config.worldgen_config import LakeConfig
from src.worldgen.features import Lake
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import BoolArray, Float64Array, Int32Array


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

    # --- 2. Connected components via BFS ---
    lake_id: Int32Array = np.full(n, -1, dtype=np.int32)
    is_lake: BoolArray = lake_mask.copy()
    lakes: list[Lake] = []
    component_id: int = 0

    # Pre-build lake membership set for O(1) lookup during outlet finding.
    # We'll rebuild it per-component inside the loop; for large lakes this
    # is still fast because we only iterate lake cells once.

    for cell_id in range(n):
        if not lake_mask[cell_id] or lake_id[cell_id] >= 0:
            continue

        component_id += 1

        # BFS from this unvisited lake cell.
        queue: deque[int] = deque()
        queue.append(cell_id)
        lake_id[cell_id] = component_id

        component_cells: list[int] = [cell_id]

        while queue:
            current: int = queue.popleft()
            for neighbor_id in geometry.neighbors_of(cell_id=current):
                neighbor_id = int(neighbor_id)
                if lake_id[neighbor_id] >= 0 or not lake_mask[neighbor_id]:
                    continue
                lake_id[neighbor_id] = component_id
                component_cells.append(neighbor_id)

        # --- 3. Build Lake object and find outlet ---
        surface_level: float = float(z_route[component_cells[0]])

        # Find the outlet cell: the boundary cell (has an outside neighbor)
        # whose outside neighbor has the lowest z_route.
        outlet_cell: int | None = _find_outlet(
            component_cells=component_cells,
            geometry=geometry,
            z_route=z_route,
        )

        lakes.append(
            Lake(
                id=component_id - 1,
                cells=component_cells,
                surface_level=surface_level,
                outlet_cell=outlet_cell,
            )
        )

    # Convert component ids to 0-based lake ids for the array.
    if lakes:
        lake_id = np.where(lake_id >= 0, lake_id - 1, -1).astype(np.int32)

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
