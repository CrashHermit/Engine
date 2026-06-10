from __future__ import annotations

import heapq

from src.worldgen.config.worldgen_config import HydrologyConfig
from src.worldgen.context import WorldContext
from src.worldgen.geometry.flow import accumulate_flux, steepest_descent
from src.worldgen.model import MeshCell, RiverSegment, VoronoiMesh


class HydrologyStage:
    """Flow routing and river-network extraction on the Voronoi mesh.

    Fills depressions (priority-flood), computes single-direction flow
    targets (steepest descent), accumulates upstream flux, and emits a
    ``RiverSegment`` for every above-threshold edge.

    Pipeline position: after ``LandmassStage``.
    """

    def __init__(self, config: HydrologyConfig) -> None:
        self._config: HydrologyConfig = config

    def run(self, ctx: WorldContext) -> None:
        mesh: VoronoiMesh = ctx.data.mesh
        self._reset_cells(mesh.cells)
        self._fill_depressions(mesh)
        flow_targets = steepest_descent(
            mesh,
            source=lambda cell: (
                cell.env.terrain.is_land and not cell.env.hydrology.is_lake
            ),
        )
        flux = accumulate_flux(
            mesh,
            flow_targets,
            source=lambda cell: cell.env.terrain.is_land,
            sink=lambda cell: (
                not cell.env.terrain.is_land or cell.env.hydrology.is_lake
            ),
        )
        threshold: float = self._river_threshold(mesh, flux)
        ctx.data.rivers.clear()
        for cell in mesh.cells:
            flux_val = flux[cell.id]
            hydrology = cell.env.hydrology
            hydrology.river_flux = float(flux_val)
            hydrology.drainage = int(flux_val)
            hydrology.is_river = cell.env.terrain.is_land and flux_val >= threshold
            downstream_id: int | None = flow_targets.get(cell.id)
            if downstream_id is not None and flux_val >= threshold:
                ctx.data.rivers.append(
                    self._make_segment(mesh, cell.id, downstream_id, flux_val)
                )

    def _river_threshold(self, mesh: VoronoiMesh, flux: list[float]) -> float:
        """Channelisation threshold from a percentile of the land-flux spread.

        Rivers are the top ``1 - river_percentile`` of land cells by drainage
        flux, floored at ``river_flux_threshold`` so faint trickles never count.
        """
        cfg = self._config
        land_flux = sorted(
            flux[cell.id] for cell in mesh.cells if cell.env.terrain.is_land
        )
        if not land_flux:
            return cfg.river_flux_threshold
        idx = min(len(land_flux) - 1, int(cfg.river_percentile * len(land_flux)))
        return max(cfg.river_flux_threshold, land_flux[idx])

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
            hydrology = cell.env.hydrology
            hydrology.drainage = 0
            hydrology.river_flux = 0.0
            hydrology.is_lake = False
            hydrology.is_river = False

    def _fill_depressions(self, mesh: VoronoiMesh) -> None:
        cells = mesh.cells
        visited: set[int] = set()
        heap: list[tuple[float, int]] = []

        for cell in cells:
            if not cell.env.terrain.is_land:
                heapq.heappush(heap, (cell.env.terrain.z, cell.id))

        if not heap:
            for cell in cells:
                heapq.heappush(heap, (cell.env.terrain.z, cell.id))

        while heap:
            elevation, cell_id = heapq.heappop(heap)
            if cell_id in visited:
                continue
            visited.add(cell_id)
            cell = cells[cell_id]
            terrain = cell.env.terrain
            if terrain.z < elevation:
                terrain.z = elevation
            if not terrain.is_land:
                cell.env.hydrology.is_lake = False
            elif terrain.z <= 0.0:
                cell.env.hydrology.is_lake = True

            for neighbor_id in cell.neighbors:
                if neighbor_id not in visited:
                    neighbor = cells[neighbor_id]
                    heapq.heappush(
                        heap, (max(elevation, neighbor.env.terrain.z), neighbor_id)
                    )
