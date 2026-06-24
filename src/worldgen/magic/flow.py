"""Mana-current direction and speed on the mesh (mirror of water/flow.py).

Phase 4 step 6: per-cell flow direction (unit vector to the receiver on the ley
potential) and a stylized speed from the potential slope and the accumulated
magic strength.  Unlike rivers these are defined on *every* cell with a receiver
(not just veins): they are the baseline 'mana currents' a future weather layer
advects over.

Speed formula (stylized):
    ``magic_flow_speed = normalize(slope**flow_slope_exp * strength**flow_strength_exp)``
"""

import numpy as np

from src.worldgen.config.worldgen_config import MagicConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta_batch
from src.worldgen.types import BoolArray, Float64Array, Int32Array


def compute_magic_flow(
    *,
    geometry: MeshGeometry,
    receiver: Int32Array,
    combined_potential: Float64Array,
    magic_strength: Float64Array,
    cfg: MagicConfig,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Compute per-cell mana-current direction and stylized speed.

    Direction is a unit vector from each cell to its receiver; speed follows
    ``slope**flow_slope_exp * strength**flow_strength_exp`` normalized to [0, 1].
    Base-level cells (``receiver == -1``) get zero direction and speed.

    Args:
        geometry: Torus mesh providing site positions and dimensions.
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        combined_potential: Per-cell ley potential (used for slope).
        magic_strength: Per-cell accumulated mana strength in [0, 1].
        cfg: Magic configuration (flow speed exponents).

    Returns:
        magic_flow_u: Per-cell unit current direction, x-component.
        magic_flow_v: Per-cell unit current direction, y-component.
        magic_flow_speed: Per-cell stylized speed, normalized to [0, 1].
    """
    site: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = len(receiver)

    flow_u: Float64Array = np.zeros(n, dtype=np.float64)
    flow_v: Float64Array = np.zeros(n, dtype=np.float64)
    flow_speed: Float64Array = np.zeros(n, dtype=np.float64)

    valid: BoolArray = receiver >= 0
    if not np.any(valid):
        return flow_u, flow_v, flow_speed

    valid_idx: Int32Array = np.flatnonzero(valid).astype(np.int32)
    src: Float64Array = site[valid_idx]
    dst: Float64Array = site[receiver[valid_idx]]

    deltas: Float64Array = torus_delta_batch(a=src, b=dst, width=width, height=height)
    dist: Float64Array = np.linalg.norm(deltas, axis=1)

    nonzero: BoolArray = dist > 0
    if np.any(nonzero):
        norm_dist: Float64Array = dist[nonzero]
        flow_u[valid_idx[nonzero]] = deltas[nonzero, 0] / norm_dist
        flow_v[valid_idx[nonzero]] = deltas[nonzero, 1] / norm_dist

    # --- slope along flow (potential drop / distance), floored positive ---
    safe_dist: Float64Array = np.where(dist > 0.0, dist, 1.0)
    p_src: Float64Array = combined_potential[valid_idx]
    p_dst: Float64Array = combined_potential[receiver[valid_idx]]
    slope: Float64Array = np.maximum((p_src - p_dst) / safe_dist, 1e-8)

    raw_speed: Float64Array = np.power(slope, cfg.flow_slope_exp) * np.power(
        magic_strength[valid_idx], cfg.flow_strength_exp
    )
    flow_speed[valid_idx] = raw_speed

    # --- normalize to [0, 1] by 95th percentile ---
    positive: BoolArray = flow_speed > 0
    if np.any(positive):
        max_speed: float = float(np.percentile(a=flow_speed[positive], q=95))
        if max_speed > 0.0:
            flow_speed = flow_speed / max_speed

    return flow_u, flow_v, np.clip(flow_speed, 0.0, 1.0)
