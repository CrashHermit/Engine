from __future__ import annotations

from collections.abc import Callable

from src.worldgen.model import MeshCell, VoronoiMesh

CellPredicate = Callable[[MeshCell], bool]


def steepest_descent(
    mesh: VoronoiMesh,
    source: CellPredicate,
) -> dict[int, int | None]:
    """Single-direction (steepest-descent) flow target per cell.

    Cells failing ``source`` map to ``None``. Every other cell flows to its
    lowest neighbour strictly below it, or ``None`` if it is a local minimum.
    """
    cells = mesh.cells
    flow: dict[int, int | None] = {}
    for cell in cells:
        if not source(cell):
            flow[cell.id] = None
            continue
        lowest_id: int | None = None
        lowest_z = cell.env.terrain.z
        for neighbor_id in cell.neighbors:
            neighbor_z = cells[neighbor_id].env.terrain.z
            if neighbor_z < lowest_z:
                lowest_z = neighbor_z
                lowest_id = neighbor_id
        flow[cell.id] = lowest_id
    return flow


def accumulate_flux(
    mesh: VoronoiMesh,
    flow: dict[int, int | None],
    source: CellPredicate,
    sink: CellPredicate,
) -> list[float]:
    """Drainage-area flux along ``flow``.

    Each ``source`` cell contributes ``1.0``, processed from high to low
    elevation so upstream flux is summed before it is passed downstream. Flux
    is not passed into a cell matching ``sink`` (ocean, lake, ...).
    """
    cells = mesh.cells
    contributors = sorted(
        (cell for cell in cells if source(cell)),
        key=lambda cell: cell.env.terrain.z,
        reverse=True,
    )
    flux = [0.0] * len(cells)
    for cell in contributors:
        flux[cell.id] += 1.0
        downstream = flow.get(cell.id)
        if downstream is None or sink(cells[downstream]):
            continue
        flux[downstream] += flux[cell.id]
    return flux
