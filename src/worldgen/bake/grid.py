"""Mesh → grid rasterization via nearest-cell Voronoi mapping."""

import numpy as np
from scipy.spatial import cKDTree

from src.core.model.environment.field_schema import PRODUCT_FIELDS
from src.worldgen.fields import Fields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Float64Array, Int32Array


def nearest_cell_per_tile(geometry: MeshGeometry, size: int) -> Int32Array:
    """Return the nearest Voronoi cell id for each grid tile center.

    Tile centers sit at ((x + 0.5) / size * width, (y + 0.5) / size * height).
    Uses scipy's periodic cKDTree so left-edge tiles can match right-edge cells.
    """
    xs: Float64Array = np.arange(start=0, stop=size, dtype=np.float64)
    ys: Float64Array = np.arange(start=0, stop=size, dtype=np.float64)
    xx, yy = np.meshgrid(xs, ys, indexing="ij")

    fx: Float64Array = (xx + 0.5) / size * geometry.width
    fy: Float64Array = (yy + 0.5) / size * geometry.height
    centers: Float64Array = np.column_stack(tup=[fx.ravel(), fy.ravel()])

    tree: cKDTree = cKDTree(
        data=geometry.sites,
        boxsize=[geometry.width, geometry.height],
    )
    _, indices = tree.query(x=centers)
    return np.asarray(a=indices, dtype=np.int32)


def bake_to_grid(fields: Fields, nearest: Int32Array) -> Fields:
    """Gather the product fields onto a grid ``Fields`` via nearest-cell indexing.

    Only ``ships_to_product`` fields (``PRODUCT_FIELDS``) cross to the grid;
    mesh-side intermediates like ``insolation`` stay at their zero allocation.
    2-D fields (``magic_channels`` ``(n, 3)``, ``biome_weights`` ``(n, n_biomes)``)
    ride the same path: ``value[nearest]`` indexes axis 0, giving ``(size*size, k)``.
    """
    grid: Fields = Fields.allocate(n=nearest.shape[0])
    for spec in PRODUCT_FIELDS:
        value = getattr(fields, spec.name)
        setattr(grid, spec.name, value[nearest])
    return grid


def bake_and_stamp(
    *,
    fields: Fields,
    geometry: MeshGeometry,
    rivers: list | None,
    size: int,
    cfg,
) -> Fields:
    """Bake mesh to grid and stamp rivers on top.

    Convenience function that calls
    ``nearest_cell_per_tile`` → ``bake_to_grid`` → ``stamp_rivers``.

    Args:
        fields: Mesh-side fields.
        geometry: Mesh geometry.
        rivers: Extracted river objects (from ``RiversStage``).
        size: Grid edge length in tiles.
        cfg: River rasterizer config.

    Returns:
        Baked-and-stamped grid ``Fields``.
    """
    from src.worldgen.bake.rivers import stamp_rivers

    nearest: Int32Array = nearest_cell_per_tile(geometry, size)
    grid: Fields = bake_to_grid(fields, nearest)
    if rivers:
        stamp_rivers(
            grid=grid,
            rivers=rivers,
            geometry=geometry,
            fields=fields,
            size=size,
            cfg=cfg,
        )
    return grid
