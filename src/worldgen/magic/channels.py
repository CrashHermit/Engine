"""Channel identity (corpus/mens/anima) seeded at sources and mixed downstream.

Phase 4 step 3.  Each cell draws a channel 'flavor' from three low-frequency
noise fields — giving clustered corpus/mens/anima-lands — and the flavors then
advect down the flow tree and blend at confluences, flow-weighted, exactly like
tributaries mixing water.  A vein's flavor is the strength-weighted mix of the
sources feeding it.
"""

import numpy as np

from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array, Int32Array, IntPArray


def seed_source_channels(
    *,
    xs: Float64Array,
    ys: Float64Array,
    corpus_noise: FractalField,
    mens_noise: FractalField,
    anima_noise: FractalField,
    frequency: float,
) -> Float64Array:
    """Per-cell headwater channel identity (n, 3), each row a distribution.

    Three independent low-frequency fields keep the triad decorrelated; mapping
    each from [-1, 1] to [0, 1] and normalizing per row gives a spatially
    clustered corpus/mens/anima composition.

    Args:
        xs: Cell-site x coordinates.
        ys: Cell-site y coordinates.
        corpus_noise: FBm field for the corpus channel.
        mens_noise: FBm field for the mens channel.
        anima_noise: FBm field for the anima channel.
        frequency: Shared spatial frequency (low → clustered flavor regions).

    Returns:
        source_channels: Per-cell channel identity, shape (n, 3), rows sum to 1.
    """
    corpus: Float64Array = (corpus_noise.sample_array(xs=xs, ys=ys, frequency=frequency) + 1.0) * 0.5
    mens: Float64Array = (mens_noise.sample_array(xs=xs, ys=ys, frequency=frequency) + 1.0) * 0.5
    anima: Float64Array = (anima_noise.sample_array(xs=xs, ys=ys, frequency=frequency) + 1.0) * 0.5

    stacked: Float64Array = np.stack(arrays=[corpus, mens, anima], axis=1)  # (n, 3)
    stacked += 1e-9  # avoid an all-zero row
    row_sum: Float64Array = stacked.sum(axis=1, keepdims=True)
    return stacked / row_sum


def mix_channels(
    *,
    receiver: Int32Array,
    potential_routed: Float64Array,
    source_emission: Float64Array,
    source_channels: Float64Array,
    accum: Float64Array,
    magic_strength: Float64Array,
) -> Float64Array:
    """Flow-weighted downstream blend of channel identities → per-cell (n, 3).

    Carry ``source_emission · source_channel`` down the same topological order as
    the strength accumulation; each cell's blended channel is that sum divided by
    its accumulated emission (``accum``).  Fade toward uniform thirds where
    ``magic_strength`` is near the floor — weak magic has no opinion.

    Args:
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        potential_routed: Per-cell routed ley potential (topological order).
        source_emission: Per-cell mana emission (the source weight).
        source_channels: Per-cell headwater channel identity (n, 3).
        accum: Per-cell accumulated emission (the blend denominator).
        magic_strength: Per-cell strength in [0, 1] (the fade factor).

    Returns:
        magic_channels: Per-cell channel composition (n, 3), rows sum to 1.
    """
    third: float = 1.0 / 3.0
    chan_acc: Float64Array = source_emission[:, None] * source_channels  # (n, 3)
    order: IntPArray = np.argsort(a=potential_routed)[::-1]

    cell_id: int
    for cell_id in order:
        r: int = int(receiver[cell_id])
        if r >= 0:
            chan_acc[r] += chan_acc[cell_id]

    safe_accum: Float64Array = np.where(accum > 0.0, accum, 1.0)
    channel_raw: Float64Array = chan_acc / safe_accum[:, None]

    # Fade toward uniform thirds where magic is weak, then renormalize.
    magic_channels: Float64Array = third + (channel_raw - third) * magic_strength[:, None]
    chan_sum: Float64Array = magic_channels.sum(axis=1, keepdims=True)
    return np.divide(
        magic_channels,
        chan_sum,
        out=np.full_like(magic_channels, third),
        where=chan_sum > 0.0,
    )
