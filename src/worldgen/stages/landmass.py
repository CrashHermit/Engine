from __future__ import annotations

from collections import deque

from src.worldgen.config.worldgen_config import LandmassConfig
from src.worldgen.context import WorldContext
from src.worldgen.data import MeshCell, VoronoiMesh

# landmass_class constants
OCEAN = 0
ISLAND = 1
LANDMASS = 2
MAJOR = 3


class LandmassStage:
    """Labels connected land components and computes coast distance.

    Assigns each land cell a ``landmass_id``, a ``landmass_class``
    (ocean / island / landmass / major) based on component size, and a
    ``coast_distance`` (BFS hops from the nearest ocean-adjacent cell).

    Pipeline position: after ``ErosionStage`` (or ``SeaLevelStage`` when
    erosion is disabled).
    """

    def __init__(self, config: LandmassConfig) -> None:
        self._config: LandmassConfig = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx
        mesh = ctx.data.mesh
        self._reset_labels(mesh.cells)
        sizes = self._label_components(mesh, ctx)
        self._classify_sizes(mesh, sizes)
        self._compute_coast_distance(mesh)
        return ctx

    def _reset_labels(self, cells: list[MeshCell]) -> None:
        for cell in cells:
            cell.landmass_id = -1
            cell.landmass_class = OCEAN
            cell.coast_distance = 0.0

    def _label_components(self, mesh: VoronoiMesh, ctx: WorldContext) -> dict[int, int]:
        cells = mesh.cells
        unvisited = {cell.id for cell in cells if cell.is_land}
        next_id = 0
        sizes: dict[int, int] = {}

        while unvisited:
            start = next(iter(unvisited))
            queue: deque[int] = deque([start])
            unvisited.discard(start)
            component_size = 0
            landmass_id = next_id
            next_id += 1

            while queue:
                cell_id = queue.popleft()
                cells[cell_id].landmass_id = landmass_id
                component_size += 1
                for neighbor_id in cells[cell_id].neighbors:
                    if neighbor_id in unvisited:
                        unvisited.discard(neighbor_id)
                        queue.append(neighbor_id)

            sizes[landmass_id] = component_size

        ctx.data.landmass_sizes = dict(sizes)
        return sizes

    def _classify_sizes(self, mesh: VoronoiMesh, sizes: dict[int, int]) -> None:
        cfg = self._config
        total_land = sum(sizes.values())
        if total_land == 0:
            return

        island_threshold = cfg.island_min_fraction * total_land
        landmass_threshold = cfg.landmass_min_fraction * total_land

        for cell in mesh.cells:
            if not cell.is_land:
                cell.landmass_class = OCEAN
                continue
            size = sizes.get(cell.landmass_id, 0)
            if size < island_threshold:
                cell.landmass_class = ISLAND
            elif size < landmass_threshold:
                cell.landmass_class = LANDMASS
            else:
                cell.landmass_class = MAJOR

    def _compute_coast_distance(self, mesh: VoronoiMesh) -> None:
        cells = mesh.cells
        queue: deque[tuple[int, float]] = deque()
        visited: set[int] = set()

        for cell in cells:
            if not cell.is_land:
                continue
            for neighbor_id in cell.neighbors:
                if not cells[neighbor_id].is_land:
                    cell.coast_distance = 0.0
                    if cell.id not in visited:
                        visited.add(cell.id)
                        queue.append((cell.id, 0.0))
                    break

        while queue:
            cell_id, dist = queue.popleft()
            cells[cell_id].coast_distance = dist
            for neighbor_id in cells[cell_id].neighbors:
                neighbor = cells[neighbor_id]
                if neighbor.is_land and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, dist + 1.0))
