"""Translate product feature geometry from mesh-cell ids to grid tile ids.

The Voronoi mesh is ephemeral — it does not ship.  Feature objects are built
during generation in mesh-cell coordinates; at assembly we rewrite their cell
references to tile ids so the shipped ``WorldData`` is self-contained (no dangling
references into the discarded mesh).  The mapping is a cell → its home tile, using
the same ``site / span * size`` formula the river rasterizer stamps with, so the
feature paths and the per-tile ``*_id`` columns agree.

Sentinels are preserved: a negative cell id (e.g. a river mouth at base level) and
``None`` outlets/mouths pass through untranslated.  Nexus/vein/river *id* fields
(``source_nexus``, ``tributary_of``, ...) are entity ids, not coordinates, and are
left alone.
"""

from dataclasses import replace

from src.core.model.environment.magic.nexus import Nexus
from src.core.model.environment.magic.vein import Vein
from src.core.model.environment.terrain.volcano import Volcano
from src.core.model.environment.water.lake import Lake
from src.core.model.environment.water.river import River
from src.worldgen.geometry.mesh import MeshGeometry


def cell_to_tile(*, geometry: MeshGeometry, size: int, cell: int) -> int:
    """Map a mesh cell id to the grid tile id containing its site (wraps on torus)."""
    site_x: float = float(geometry.sites[cell, 0])
    site_y: float = float(geometry.sites[cell, 1])
    tile_x: int = int(site_x / geometry.width * size) % size
    tile_y: int = int(site_y / geometry.height * size) % size
    return tile_y * size + tile_x


def _tile(geometry: MeshGeometry, size: int, cell: int) -> int:
    """Translate one cell id, preserving negative sentinels."""
    if cell < 0:
        return cell
    return cell_to_tile(geometry=geometry, size=size, cell=cell)


def _tiles(geometry: MeshGeometry, size: int, cells: list[int]) -> list[int]:
    """Translate a path of cell ids to tile ids (1:1, payload alignment preserved)."""
    return [_tile(geometry, size, cell) for cell in cells]


def features_to_tiles(
    *,
    geometry: MeshGeometry,
    size: int,
    rivers: list[River],
    lakes: list[Lake],
    veins: list[Vein],
    nexuses: list[Nexus],
    volcanoes: list[Volcano],
) -> tuple[list[River], list[Lake], list[Vein], list[Nexus], list[Volcano]]:
    """Return new feature lists with all cell references rewritten to tile ids."""
    rivers_t: list[River] = [
        replace(r, cells=_tiles(geometry, size, r.cells), mouth=_tile(geometry, size, r.mouth))
        for r in rivers
    ]
    lakes_t: list[Lake] = [
        replace(
            lake,
            cells=_tiles(geometry, size, lake.cells),
            outlet_cell=(
                None if lake.outlet_cell is None
                else _tile(geometry, size, lake.outlet_cell)
            ),
        )
        for lake in lakes
    ]
    veins_t: list[Vein] = [
        replace(v, cells=_tiles(geometry, size, v.cells)) for v in veins
    ]
    nexuses_t: list[Nexus] = [
        replace(nx, cell=_tile(geometry, size, nx.cell)) for nx in nexuses
    ]
    volcanoes_t: list[Volcano] = [
        replace(vol, cell=_tile(geometry, size, vol.cell)) for vol in volcanoes
    ]
    return rivers_t, lakes_t, veins_t, nexuses_t, volcanoes_t
