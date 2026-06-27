"""River rasterizer: stamp river paths onto the tile grid.

Phase 3 step 6 — Rasterize to the grid.
Runs **after** the generic ``bake_to_grid`` and overwrites river tiles.
"""

import math

import numpy as np

from src.worldgen.config.worldgen_config import RiverConfig
from src.worldgen.fields import Fields
from src.core.model.environment.water.river import River
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Float64Array


def stamp_rivers(
    *,
    grid: Fields,
    rivers: list[River],
    geometry: MeshGeometry,
    fields: Fields,
    size: int,
    cfg: RiverConfig,
) -> None:
    """Walk each river's site-to-site segments, stamping disks onto grid tiles.

    For each river, each consecutive cell-pair forms a segment.  We step
    along the segment in small increments (step ≈ 0.5 tile) and at every
    step stamp a disk whose radius follows ``w = clip(w_scale * sqrt(q),
    min_w, max_w)`` — *sqrt* because river width grows sub-linearly with
    flow.

    On contested tiles the **larger discharge** wins ``river_id`` and
    ``flow_*`` fields; ``is_river`` is set to ``True`` for any stamp that
    touches a tile.

    Args:
        grid: Tile-grid fields, already baked via ``bake_to_grid``.
        rivers: Extracted river objects (from ``RiversStage``).
        geometry: Mesh geometry providing site positions.
        fields: Mesh fields (provides flow_u/flow_v/flow_speed per cell).
        size: Grid edge length in tiles.
        cfg: River rasterizer config (width scale, min/max width).
    """
    n: int = size * size
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height

    # Ensure river identity fields start clean.
    grid.is_river = np.full(shape=n, fill_value=False, dtype=bool)
    grid.river_id = np.full(shape=n, fill_value=-1, dtype=np.int32)

    # Pre-compute tile coordinates for every mesh cell to avoid
    # repeated division in the inner loop.
    cell_tile_x: Float64Array = (sites[:, 0] / width) * size
    cell_tile_y: Float64Array = (sites[:, 1] / height) * size

    for river in rivers:
        cells = river.cells
        discharge_along = river.discharge

        for seg_idx in range(len(cells) - 1):
            cell_a = cells[seg_idx]
            cell_b = cells[seg_idx + 1]
            q = float(discharge_along[seg_idx])

            # --- segment endpoints in tile coordinates ---
            tx_a = float(cell_tile_x[cell_a])
            ty_a = float(cell_tile_y[cell_a])
            tx_b = float(cell_tile_x[cell_b])
            ty_b = float(cell_tile_y[cell_b])

            # Minimum-image displacement on the torus.
            dx_total = tx_b - tx_a
            dx_total -= size * round(dx_total / size)
            dy_total = ty_b - ty_a
            dy_total -= size * round(dy_total / size)

            seg_len = math.sqrt(dx_total * dx_total + dy_total * dy_total)
            if seg_len < 1e-10:
                continue  # degenerate segment

            # --- radius for this segment ---
            radius = min(
                max(cfg.w_scale * math.sqrt(max(q, 0.0)), cfg.min_w),
                cfg.max_w,
            )
            r_int = int(math.ceil(radius))

            # --- step along the segment ---
            step_size = max(0.3, 0.5)  # ≈ 0.5 tile units
            n_steps = max(1, int(math.ceil(seg_len / step_size)))
            dx_step = dx_total / n_steps
            dy_step = dy_total / n_steps

            # Read flow values directly from the mesh fields.
            mesh_flow_u = float(fields.flow_u[cell_a])
            mesh_flow_v = float(fields.flow_v[cell_a])
            mesh_flow_speed = float(fields.flow_speed[cell_a])

            # Stamp disks at each step position.
            for step_i in range(n_steps + 1):
                tx = tx_a + step_i * dx_step
                ty = ty_a + step_i * dy_step

                cx = int(tx) % size
                cy = int(ty) % size

                _stamp_disk_around(
                    grid=grid,
                    cx=cx,
                    cy=cy,
                    r_int=r_int,
                    size=size,
                    river_id=river.id,
                    discharge=q,
                    flow_u=mesh_flow_u,
                    flow_v=mesh_flow_v,
                    flow_speed=mesh_flow_speed,
                )


def _stamp_disk_around(
    *,
    grid: Fields,
    cx: int,
    cy: int,
    r_int: int,
    size: int,
    river_id: int,
    discharge: float,
    flow_u: float,
    flow_v: float,
    flow_speed: float,
) -> None:
    """Stamp a disk centered at tile (cx, cy) with the given integer radius.

    For each tile within the disk, if the incoming discharge is larger
    than the current tile's discharge, overwrite all river fields.
    """
    half = min(r_int, size // 2)

    for dy in range(-half, half + 1):
        ny = (cy + dy) % size
        dy2 = dy * dy
        for dx in range(-half, half + 1):
            nx = (cx + dx) % size
            if dx * dx + dy2 > r_int * r_int:
                continue
            idx = ny * size + nx
            # Larger discharge wins (the "wetter stamp" rule).
            if discharge > float(grid.discharge[idx]):
                grid.is_river[idx] = True
                grid.river_id[idx] = river_id
                grid.discharge[idx] = discharge
                grid.flow_u[idx] = flow_u
                grid.flow_v[idx] = flow_v
                grid.flow_speed[idx] = flow_speed
