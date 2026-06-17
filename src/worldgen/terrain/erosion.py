from __future__ import annotations

import numpy as np

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import Float64Array, Int32Array, IntPArray


def stream_power_pass(
    *,
    z: Float64Array,
    z_route: Float64Array,
    receiver: Int32Array,
    drainage: Float64Array,
    uplift: Float64Array,
    geometry: MeshGeometry,
    cfg: ErosionConfig,
) -> None:
    """Single implicit stream-powered erosion pass.

    Processes cells from lowest to highest ``z_route`` so every
    receiver's new height is available before its donors are
    processed (Braun & Willett 2013).

    The implicit scheme is unconditionally stable: each cell's new
    height is a weighted average of its uplifted position and the
    receiver's already-updated height, so it can approach but
    never overshoot the receiver.

    Args:
        z: Per-cell ground elevation (mutated in place).
        z_route: Water-surface elevation from ``priority_flood``.
        receiver: Downstream cell id; ``-1`` = base level.
        drainage: Per-cell upstream area from
            ``accumulate_drainage``.
        uplift: Tectonic push-up rate per cell.
        geometry: Torus mesh with CSR adjacency.
        cfg: Erosion parameters (``dt``, ``K``, ``m``).
    """
    order: IntPArray = np.argsort(a=z_route)

    for cell_id in order:
        r: int = int(receiver[cell_id])

        if r < 0:
            # Base-level cell (ocean / pit) — no downstream receiver.
            continue

        if z[cell_id] < z_route[cell_id]:
            # Submerged cell (under lake water) — channel erosion
            # does not occur on submerged rock.
            continue

        # --- implicit stream-power update (Braun & Willett 2013) ---
        # Extract scalars as Python float before arithmetic so
        # every local variable is strongly typed (repo convention).
        z_i: float = float(z[cell_id])
        z_r: float = float(z[r])
        d_i: float = float(drainage[cell_id])
        u_i: float = float(uplift[cell_id])

        # Torus-aware distance from this cell to its receiver.
        dist: float = torus_distance(
            a=geometry.sites[cell_id],
            b=geometry.sites[r],
            width=geometry.width,
            height=geometry.height,
        )

        # Stream-power weight: f = dt * K * A^m / L
        f: float = cfg.dt * cfg.K * (d_i ** cfg.m) / dist

        # Implicit update: weighted average of the uplifted height
        # and the receiver's already-computed new height.
        z[cell_id] = (z_i + cfg.dt * u_i + f * z_r) / (1.0 + f)
