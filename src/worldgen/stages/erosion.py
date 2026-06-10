from __future__ import annotations

from src.worldgen.config.worldgen_config import ErosionConfig, SeaLevelConfig
from src.worldgen.context import WorldContext
from src.worldgen.model import VoronoiMesh


class ErosionStage:
    """Optional stream-power and thermal erosion on the Voronoi mesh.

    When ``config.enabled`` is False this stage is a no-op.  Otherwise it
    iterates ``config.iterations`` passes of:

    * **Stream-power erosion**: cells with high upstream drainage area and
      steep slopes lose elevation, carving valleys.
    * **Thermal erosion**: elevation is diffused toward the talus angle
      across neighbours, softening sharp ridges and cliffs.

    After erosion the sea-level percentile cut is re-derived so that
    ``target_land_fraction`` is honoured on the eroded topography.

    Pipeline position: after ``SeaLevelStage``, before ``LandmassStage``.
    """

    def __init__(self, config: ErosionConfig, sea_level: SeaLevelConfig) -> None:
        self._config = config
        self._sea_level = sea_level

    def run(self, ctx: WorldContext) -> WorldContext:
        if not self._config.enabled:
            return ctx

        mesh = ctx.data.mesh
        for _ in range(self._config.iterations):
            flow_targets, flux = self._flow_and_flux(mesh)
            self._stream_power(mesh, flow_targets, flux)
            self._thermal(mesh)

        # Re-apply sea level on the eroded surface
        cells = mesh.cells
        sorted_z = sorted(cell.env.terrain.z for cell in cells)
        idx = int((1.0 - self._sea_level.target_land_fraction) * len(sorted_z))
        idx = max(0, min(idx, len(sorted_z) - 1))
        sea_level = sorted_z[idx]
        for cell in cells:
            cell.env.terrain.is_land = cell.env.terrain.z >= sea_level

        return ctx

    # ------------------------------------------------------------------

    def _flow_and_flux(
        self, mesh: VoronoiMesh
    ) -> tuple[dict[int, int | None], list[float]]:
        cells = mesh.cells
        flow: dict[int, int | None] = {}
        for cell in cells:
            if not cell.env.terrain.is_land:
                flow[cell.id] = None
                continue
            best: int | None = None
            best_z = cell.env.terrain.z
            for nid in cell.neighbors:
                if cells[nid].env.terrain.z < best_z:
                    best_z = cells[nid].env.terrain.z
                    best = nid
            flow[cell.id] = best

        land_cells = sorted(
            (c for c in cells if c.env.terrain.is_land),
            key=lambda c: c.env.terrain.z,
            reverse=True,
        )
        flux = [0.0] * len(cells)
        for cell in land_cells:
            flux[cell.id] += 1.0
            ds = flow.get(cell.id)
            if ds is not None and cells[ds].env.terrain.is_land:
                flux[ds] += flux[cell.id]
        return flow, flux

    def _stream_power(
        self,
        mesh: VoronoiMesh,
        flow: dict[int, int | None],
        flux: list[float],
    ) -> None:
        k = self._config.stream_power
        cells = mesh.cells
        for cell in cells:
            terrain = cell.env.terrain
            if not terrain.is_land:
                continue
            ds = flow.get(cell.id)
            if ds is None:
                continue
            slope = max(0.0, terrain.z - cells[ds].env.terrain.z)
            erosion = k * (flux[cell.id] ** 0.5) * slope * 0.001
            terrain.z = max(0.0, terrain.z - erosion)

    def _thermal(self, mesh: VoronoiMesh) -> None:
        talus = self._config.thermal_talus
        cells = mesh.cells
        deltas = [0.0] * len(cells)
        for cell in cells:
            if not cell.env.terrain.is_land:
                continue
            for nid in cell.neighbors:
                neighbor = cells[nid]
                diff = cell.env.terrain.z - neighbor.env.terrain.z
                if diff > talus:
                    transfer = (diff - talus) * 0.25
                    deltas[cell.id] -= transfer
                    deltas[nid] += transfer
        for cell in cells:
            cell.env.terrain.z += deltas[cell.id]
