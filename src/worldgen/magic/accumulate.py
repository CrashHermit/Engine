"""Accumulate mana emission down the ley flow tree (mirror of discharge).

Phase 4 step 2.  This is the river drainage loop with one change: each cell
contributes its ``source_emission`` (the ley-mantle's '+' regions are mana's
rainfall) instead of ``1.0``.  Processing from highest to lowest
``potential_routed`` guarantees every donor is complete before it hands off, so
each cell is visited exactly once.
"""

import numpy as np

from src.worldgen.config.worldgen_config import MagicConfig
from src.worldgen.types import Float64Array, Int32Array, IntPArray


def compute_source_emission(
    *,
    ley_mantle: Float64Array,
    cfg: MagicConfig,
) -> Float64Array:
    """Per-cell mana emission: the ley-mantle's '+' regions plus an ambient floor.

    The ley-mantle's above-mean ('+') regions are mana's 'rainfall'; the floor
    keeps dead zones faintly alive (mirror of uniform rain).

    Args:
        ley_mantle: Per-cell ley-mantle value (roughly [-1, 1]).
        cfg: Magic configuration (ambient floor).

    Returns:
        source_emission: Per-cell mana emission (>= ambient_floor).
    """
    return (
        np.clip(ley_mantle - float(ley_mantle.mean()), 0.0, None) + cfg.ambient_floor
    )


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


def normalize_strength(*, accum: Float64Array) -> Float64Array:
    """Log-compress raw accumulation into ``magic_strength`` in [0, 1].

    Raw accumulation spans 1 to thousands; a ``log1p`` compression scaled by the
    maximum gives a legible [0, 1] field (the same log the river viewer applies
    to discharge, here baked into the field itself).

    Args:
        accum: Per-cell raw accumulated mana flow.

    Returns:
        magic_strength: Per-cell intensity in [0, 1].
    """
    accum_max: float = float(accum.max())
    if accum_max <= 0.0:
        return np.zeros_like(accum)
    return np.clip(np.log1p(accum) / np.log1p(accum_max), 0.0, 1.0)
