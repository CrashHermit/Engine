"""Accumulate mana emission down the ley flow tree (mirror of discharge).

Phase 4 step 2.  This is the river drainage loop with one change: each cell
contributes its ``source_emission`` (the ley-mantle's '+' regions are mana's
rainfall) instead of ``1.0``.  Processing from highest to lowest
``potential_routed`` guarantees every donor is complete before it hands off, so
each cell is visited exactly once.
"""

import numpy as np

from src.worldgen.types import Float64Array, Int32Array, IntPArray


def accumulate_strength(
    *,
    receiver: Int32Array,
    potential_routed: Float64Array,
    source_emission: Float64Array,
) -> Float64Array:
    """Accumulate mana emission along the receiver flow tree.

    Every cell contributes its own emission and passes its accumulated total
    downstream to its receiver.  The returned array is the *raw* accumulation
    (1 to thousands); the stage log-normalizes it to ``magic_strength`` in
    ``[0, 1]``.

    Args:
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        potential_routed: Per-cell routed ley potential (for topological order).
        source_emission: Per-cell mana emission (the source/"rainfall" weight).

    Returns:
        accum: Per-cell accumulated mana flow (float64, raw).
    """
    accum: Float64Array = source_emission.astype(np.float64).copy()
    order: IntPArray = np.argsort(a=potential_routed)[::-1]

    for cell_id in order:
        r: int = int(receiver[cell_id])
        if r >= 0:
            accum[r] += accum[cell_id]

    return accum
