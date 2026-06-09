from __future__ import annotations

import heapq

from src.worldgen.config.worldgen_config import HydrologyConfig
from src.worldgen.context import WorldContext
from src.worldgen.data import MeshCell, RiverSegment, VoronoiMesh


class HydrologyStage:
    """Flow routing and river-network extraction on the Voronoi mesh.

    Fills depressions (priority-flood), computes single-direction flow
    targets (steepest descent), accumulates upstream flux, and emits a
    ``RiverSegment`` for every above-threshold edge.

    Pipeline position: after ``LandmassStage``.
    """

    def __init__(self, config: HydrologyConfig) -> None:
        self._config: HydrologyConfig = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx
        mesh = ctx.data.mesh
        self._reset_cells(mesh.cells)
        self._fill_depressions(mesh)
        flow_targets = self._compute_flow_targets(mesh)
        flux = self._accumulate_flux(mesh, flow_targets)
        threshold = self._config.river_flux_threshold
        ctx.data.rivers.clear()
        for cell in mesh.cells:
            cell.river_flux = float(flux[cell.id])
            cell.drainage = int(flux[cell.id])
            cell.is_river = cell.is_land and flux[cell.id] >= threshold
            downstream_id = flow_targets.get(cell.id)
            if downstream_id is not None and flux[cell.id] >= threshold:
                ctx.data.rivers.append(
                    self._make_segment(mesh, cell.id, downstream_id, flux[cell.id])
                )
        return ctx

    def _make_segment(
        self,
        mesh: VoronoiMesh,
        from_id: int,
        to_id: int,
        flux: float,
    ) -> RiverSegment:
        sx, sy = mesh.cells[from_id].site
        ex, ey = mesh.cells[to_id].site
        best_dx = min((-mesh.width, 0.0, mesh.width), key=lambda d: abs(ex + d - sx))
        best_dy = min((-mesh.height, 0.0, mesh.height), key=lambda d: abs(ey + d - sy))
        return RiverSegment(
            start=(sx, sy),
            end=(ex + best_dx, ey + best_dy),
            flux=flux,
        )

    def _reset_cells(self, cells: list[MeshCell]) -> None:
        for cell in cells:
            cell.drainage = 0
            cell.river_flux = 0.0
            cell.is_lake = False
            cell.is_river = False

    def _fill_depressions(self, mesh: VoronoiMesh) -> None:
        cells = mesh.cells
        visited: set[int] = set()
        heap: list[tuple[float, int]] = []

        for cell in cells:
            if not cell.is_land:
                heapq.heappush(heap, (cell.z, cell.id))

        if not heap:
            for cell in cells:
                heapq.heappush(heap, (cell.z, cell.id))

        while heap:
            elevation, cell_id = heapq.heappop(heap)
            if cell_id in visited:
                continue
            visited.add(cell_id)
            cell = cells[cell_id]
            if cell.z < elevation:
                cell.z = elevation
            if not cell.is_land:
                cell.is_lake = False
            elif cell.z <= 0.0:
                cell.is_lake = True

            for neighbor_id in cell.neighbors:
                if neighbor_id not in visited:
                    neighbor = cells[neighbor_id]
                    heapq.heappush(heap, (max(elevation, neighbor.z), neighbor_id))

    def _compute_flow_targets(self, mesh: VoronoiMesh) -> dict[int, int | None]:
        flow: dict[int, int | None] = {}
        for cell in mesh.cells:
            if not cell.is_land or cell.is_lake:
                flow[cell.id] = None
                continue
            lowest_id: int | None = None
            lowest_z = cell.z
            for neighbor_id in cell.neighbors:
                neighbor = mesh.cells[neighbor_id]
                if neighbor.z < lowest_z:
                    lowest_z = neighbor.z
                    lowest_id = neighbor_id
            flow[cell.id] = lowest_id
        return flow

    def _accumulate_flux(
        self,
        mesh: VoronoiMesh,
        flow_targets: dict[int, int | None],
    ) -> list[float]:
        land_cells = [cell for cell in mesh.cells if cell.is_land]
        land_cells.sort(key=lambda cell: cell.z, reverse=True)
        flux = [0.0] * len(mesh.cells)

        for cell in land_cells:
            flux[cell.id] += 1.0
            downstream = flow_targets.get(cell.id)
            if downstream is None:
                continue
            downstream_cell = mesh.cells[downstream]
            if not downstream_cell.is_land or downstream_cell.is_lake:
                continue
            flux[downstream] += flux[cell.id]

        return flux
