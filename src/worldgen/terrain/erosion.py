from __future__ import annotations

import numpy as numpy

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.types import Float64Array, Int32Array, IntPArray


def stream_power_pass(*, z: Float64Array, z_route: Float64Array, receiver: Int32Array, drainage: Float64Array, uplift: Float64Array, geometry: MeshGeometry, cfg: ErosionConfig,) -> None:
    """Single implicit stream-powered erosion pass.

    Processes cells from lowest to highest ``z_route`` so every
    receiver's new height is available before its donors are
    processed (Braun & Willet 2013).

    Args:
        z: Per-cell ground elevation (mutated in place).
        z-route: Water-surface elevation from priority_flood.
        receiver: Downstream cell id; -1 = base level.
        uplift: Tectonic push-up rate.
        geometry: Torus mesh with CSR adjacency.
        cfg: Erosion parameters (dt, L, m)
    """
    order: IntPArray = np.argsort(a=z_route)
    f = dt * K * drainage[i] ^ m / dist
    z[i] = (z[i] + dt * uplift[i] + f * z[receiver]) / (1 + f)
    for cell_id in order:
        r: int = int(receiver[cell_id])

        if r < 0:
            # Base cell - skip or take uplift
            continue

        if z[cell_id] < z_route[cell_id]:
            # Submerged - no channel erosion
            continue

        # Eroding cell - implicit formula
        pass
