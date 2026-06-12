from __future__ import annotations

import numpy as np
from dataclasses import fields as dataclass_fields
from scipy.spatial import cKDTree

from src.worldgen.fields import GridFields, MeshFields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Float64Array, Int32Array


def nearest_cell_per_tile(geometry: MeshGeometry, size: int) -> Int32Array:
    """Return the nearest Voroni cell id for each grid tile center
    
    Tile cneters sit at ((x + 0.5 / size * width, (y + 0.5) / size * height).
    Use scipy's periodic ckdtree to left-edge tiles can match right-edge cells.
    """
    xs: Float64Array = np.arange(start=0, stop=size, dtype=np.float64) # start is default 0 and start is n - 1 so size - 1 in this case
    ys: Float64Array = np.arange(start=0, stop=size, dtype=np.float64)
    xx, yy = np.meshgrid(xs, ys, indexing="ij")

    fx: Float64Array = (xx + 0.5) / size * geometry.width
    fy: Float64Array = (yy + 0.5) / size * geometry.height
    centers: Float64Array = np.column_stack(tup=[fx.ravel(), fy.ravel()]) # ravel here puts all of these in a line, all x coords in order and all y coords in the same order, 1d

    tree: cKDTree = cKDTree(
        data=geometry.sites,
        boxsize=[geometry.width, geometry.height],
    )
    _, indices = tree.query(x=centers)
    return np.asarray(a=indices, dtype=np.int32)

def bake_to_grid(fields: MeshFields, nearest: Int32Array) -> GridFields:
    """Copy every mesh field onto the grid via nearest-cell fancy indexing."""
    grid: GridFields = GridFields.allocate(n=nearest.shape[0])
    for f in dataclass_fields(class_or_instance=MeshFields):
        setattr(grid, f.name, getattr(fields, f.name)[nearest])
    return grid