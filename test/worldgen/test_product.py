"""The shipped WorldData is self-contained: feature geometry is in tile space.

After the bake, no product object may reference a mesh-cell id — the mesh is
ephemeral and does not ship.  All cell references must be valid tile ids (or a
preserved negative / None sentinel).
"""

from dataclasses import replace

import pytest

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline

SEEDS: list[int] = [1, 7, 42]


def _world(seed: int):
    cfg: WorldgenConfig = replace(WorldgenConfig(), mesh=MeshConfig(cell_count=500))
    return WorldgenPipeline(cfg).run(seed=seed, size=40)


@pytest.mark.parametrize("seed", SEEDS)
def test_feature_geometry_is_tile_space(seed: int) -> None:
    """Every shipped feature cell reference is a valid tile id (or a sentinel)."""
    world = _world(seed)
    n_tiles: int = world.size * world.size

    def valid(tile_id: int, *, allow_negative: bool) -> bool:
        if tile_id < 0:
            return allow_negative
        return tile_id < n_tiles

    for r in world.rivers:
        assert all(valid(c, allow_negative=False) for c in r.cells)
        assert valid(r.mouth, allow_negative=True)
        assert len(r.cells) == len(r.discharge)  # payload stays aligned
    for lake in world.lakes:
        assert all(valid(c, allow_negative=False) for c in lake.cells)
        assert lake.outlet_cell is None or valid(lake.outlet_cell, allow_negative=False)
    for v in world.veins:
        assert all(valid(c, allow_negative=False) for c in v.cells)
    for nx in world.nexuses:
        assert valid(nx.cell, allow_negative=False)
    for vol in world.volcanoes:
        assert valid(vol.cell, allow_negative=False)


def test_mesh_is_denser_than_grid_proving_translation() -> None:
    """A run where the mesh has fewer cells than tiles still ships tile-space ids.

    With cell_count=500 and size=40 (1600 tiles) the mesh is *sparser* than the
    grid, so an untranslated mesh id would still fit the tile range by luck.  This
    run uses a dense mesh (more cells than tiles) so an untranslated mesh id would
    exceed the tile range — catching a regression where translation is skipped.
    """
    cfg: WorldgenConfig = replace(WorldgenConfig(), mesh=MeshConfig(cell_count=3000))
    world = WorldgenPipeline(cfg).run(seed=3, size=40)
    n_tiles: int = world.size * world.size
    for r in world.rivers:
        assert all(c < n_tiles for c in r.cells), "river cell id exceeds tile range"
