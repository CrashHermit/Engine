from __future__ import annotations

from src.worldgen.config.worldgen_config import ErosionConfig, SeaLevelConfig
from src.worldgen.context import WorldContext
from src.worldgen.geometry.flow import accumulate_flux, steepest_descent
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

    def run(self, ctx: WorldContext) -> None:
        if not self._config.enabled:
            return

        mesh = ctx.data.mesh
        for _ in range(self._config.iterations):
            flow_targets = steepest_descent(
                mesh, source=lambda cell: cell.env.terrain.is_land
            )
            flux = accumulate_flux(
                mesh,
                flow_targets,
                source=lambda cell: cell.env.terrain.is_land,
                sink=lambda cell: not cell.env.terrain.is_land,
            )
            self._stream_power(mesh, flow_targets, flux)
            self._thermal(mesh)

        # Re-derive sea level on the eroded surface and re-zero elevation so the
        # "0 = sea level" invariant (relied on by ClimateStage's lapse rate)
        # still holds after erosion has reshaped the terrain.
        cells = mesh.cells
        sorted_z = sorted(cell.env.terrain.z for cell in cells)
        idx = int((1.0 - self._sea_level.target_land_fraction) * len(sorted_z))
        idx = max(0, min(idx, len(sorted_z) - 1))
        sea_level = sorted_z[idx]
        for cell in cells:
            terrain = cell.env.terrain
            terrain.is_land = terrain.z >= sea_level
            terrain.z -= sea_level

    # ------------------------------------------------------------------

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
