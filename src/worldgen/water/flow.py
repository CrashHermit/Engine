"""Flow direction and speed on the mesh.

Phase 3 step 5: per-cell flow direction (unit vector to receiver) and
stylized Manning-inspired speed derived from slope and discharge.

Direction formula:
    ``flow_u/flow_v = unit(torus_delta(site[i], site[receiver[i]]))``

Speed formula (Manning-flavored stylization):
    ``flow_speed = normalize(slope_along_flow**0.3 * discharge**0.2)``

where ``slope_along_flow = (z[i] - z[receiver]) / dist``.  Inside lakes
the slope floor is raised to a tiny epsilon so lake-crossing reaches
come out near-still.

The exponents ``0.3`` and ``0.2`` are part of the stylized formula
(roughly analogous to Manning's n ≈ 0.3 and area exponent ≈ 0.2) and
are intentionally config-free.
"""

import numpy as np

from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_delta_batch
from src.worldgen.types import BoolArray, Float64Array, Int32Array
from src.worldgen.context import WorldContext


def compute_flow(
    *,
    geometry: MeshGeometry,
    receiver: Int32Array,
    elevation: Float64Array,
    discharge: Float64Array,
    is_lake: BoolArray,
    is_river: BoolArray | None = None,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Compute per-cell flow direction and stylized Manning speed.

    Direction is a unit vector pointing from each cell to its receiver.
    Speed follows a Manning-flavored formula:
    ``slope**0.3 * discharge**0.2``, normalized to [0, 1] by percentile.

    Cells with ``receiver == -1`` (base level) get zero direction and
    speed.  Non-river cells may be zeroed if ``is_river`` is provided.

    Args:
        geometry: Torus mesh providing site positions and dimensions.
        receiver: Per-cell downstream cell id; ``-1`` = base level.
        elevation: Per-cell terrain elevation (used for slope).
        discharge: Per-cell rain-weighted water flow.
        is_lake: Boolean mask identifying lake cells.
        is_river: Optional boolean mask identifying river cells.  When
            provided, non-river cells are zeroed in all outputs.

    Returns:
        flow_u: Per-cell unit flow direction, x-component.
        flow_v: Per-cell unit flow direction, y-component.
        flow_speed: Per-cell stylized speed, normalized to [0, 1].
    """
    site: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    n: int = len(receiver)

    # --- 1. Compute direction vectors and distances ---
    flow_u: Float64Array = np.zeros(n, dtype=np.float64)
    flow_v: Float64Array = np.zeros(n, dtype=np.float64)

    # Identify cells with valid receivers.
    valid: BoolArray = receiver >= 0
    if not np.any(valid):
        return flow_u, flow_v, np.zeros(n, dtype=np.float64)

    valid_idx: Int32Array = np.flatnonzero(valid).astype(np.int32)
    src: Float64Array = site[valid_idx]
    dst: Float64Array = site[receiver[valid_idx]]

    # Vectorized minimum-image delta and distance.
    deltas: Float64Array = torus_delta_batch(
        a=src, b=dst, width=width, height=height
    )
    dist: Float64Array = np.linalg.norm(deltas, axis=1)

    # Normalize to unit vectors; skip zero-length segments.
    nonzero: BoolArray = dist > 0
    if np.any(nonzero):
        norm_dist: Float64Array = dist[nonzero]
        flow_u[valid_idx[nonzero]] = deltas[nonzero, 0] / norm_dist
        flow_v[valid_idx[nonzero]] = deltas[nonzero, 1] / norm_dist

    # --- 2. Compute slope along flow ---
    # slope = (z[i] - z[receiver]) / dist, floored at epsilon.
    z_src: Float64Array = elevation[valid_idx]
    z_dst: Float64Array = elevation[receiver[valid_idx]]
    raw_slope: Float64Array = (z_src - z_dst) / dist

    # Floor inside lakes to a tiny epsilon so lake-crossing reaches are
    # near-still; outside lakes, floor to a small positive number.
    epsilon_lake: float = 1e-6
    epsilon_land: float = 1e-8
    lake_mask_valid: BoolArray = is_lake[valid_idx]

    slope: Float64Array = np.where(
        lake_mask_valid,
        np.maximum(raw_slope, epsilon_lake),
        np.maximum(raw_slope, epsilon_land),
    )

    # --- 3. Compute stylized speed ---
    # speed = slope**0.3 * discharge**0.2
    raw_speed: Float64Array = np.power(slope, 0.3) * np.power(
        discharge[valid_idx], 0.2
    )

    # Zero speed for base-level cells (receiver == -1).
    speed_full: Float64Array = np.zeros(n, dtype=np.float64)
    speed_full[valid_idx] = raw_speed

    # --- 4. Normalize to [0, 1] by 95th-percentile ---
    non_zero: BoolArray = speed_full > 0
    if np.any(non_zero):
        max_speed: float = float(np.percentile(a=speed_full[non_zero], q=95))
        if max_speed > 0:
            flow_speed: Float64Array = speed_full / max_speed
        else:
            flow_speed = speed_full
    else:
        flow_speed = speed_full

    # Clip to [0, 1] to handle edge cases.
    flow_speed = np.clip(flow_speed, 0.0, 1.0)

    # --- 5. Zero non-river cells if is_river is provided ---
    if is_river is not None:
        flow_u[~is_river] = 0.0
        flow_v[~is_river] = 0.0
        flow_speed[~is_river] = 0.0

    return flow_u, flow_v, flow_speed


class FlowStage:
    """Compute flow direction (flow_u/flow_v) and stylized speed (flow_speed).

    Phase 3 step 5: for each river/land cell, compute a unit direction
    vector pointing to the receiver and a Manning-flavored stylized speed
    derived from slope and discharge.

    Pipeline order: after LakesStage (is_lake must be populated).
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute flow direction and speed; write flow_u, flow_v, flow_speed."""
        # --- prerequisites ---
        receiver_field = ctx.fields.receiver
        if receiver_field is None:
            msg: str = "receiver must be set before FlowStage"
            raise RuntimeError(msg)
        receiver = receiver_field

        elevation_field = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before FlowStage"
            raise RuntimeError(msg)
        elevation = elevation_field

        discharge_field = ctx.fields.discharge
        if discharge_field is None:
            msg: str = "discharge must be set before FlowStage"
            raise RuntimeError(msg)
        discharge = discharge_field

        is_lake_field = ctx.fields.is_lake
        if is_lake_field is None:
            msg: str = "is_lake must be set before FlowStage"
            raise RuntimeError(msg)
        is_lake = is_lake_field

        is_river_field = ctx.fields.is_river

        # --- Compute flow ---
        flow_u, flow_v, flow_speed = compute_flow(
            geometry=ctx.geometry,
            receiver=receiver,
            elevation=elevation,
            discharge=discharge,
            is_lake=is_lake,
            is_river=is_river_field,
        )

        ctx.fields.flow_u = flow_u
        ctx.fields.flow_v = flow_v
        ctx.fields.flow_speed = flow_speed
