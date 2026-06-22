"""Rain-weighted discharge accumulation on the final terrain flow tree.

This is Phase 1's drainage loop with one change: each cell contributes
``precipitation[i]`` instead of ``1.0``.  Ocean cells are zeroed —
discharge is a land concept.
"""

import numpy as np

from src.worldgen.types import BoolArray, Float64Array, Int32Array


def accumulate_discharge(
    *,
    receiver: Int32Array,
    z_route: Float64Array,
    precipitation: Float64Array,
    is_land: BoolArray,
) -> Float64Array:
    """Accumulate rain-weighted water flow along the receiver flow tree.

    Every land cell contributes its own precipitation value and passes its
    accumulated total downstream to its receiver.  Processing from highest
    to lowest ``z_route`` guarantees every donor is complete before it hands
    off its total, so each cell is visited exactly once.

    Ocean cells receive zero discharge.

    Args:
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        z_route: Per-cell water-surface elevation from
            ``priority_flood`` (float64).  Used only for
            topological ordering.
        precipitation: Per-cell rainfall amount [0, 1].
        is_land: Boolean mask identifying land cells.

    Returns:
        discharge: Per-cell rain-weighted water flow (float64).
            Ocean cells are zeroed.
    """
    n: int = len(receiver)
    discharge: Float64Array = np.where(is_land, precipitation, 0.0)
    order: Int32Array = np.argsort(a=z_route)[::-1].astype(np.int32)

    for cell_id in order:
        r: int = int(receiver[cell_id])
        if r >= 0:
            discharge[r] += discharge[cell_id]

    # Ocean cells accumulate the totals of land cells draining into them;
    # zero them again — discharge is a land concept.
    discharge[~is_land] = 0.0

    return discharge
