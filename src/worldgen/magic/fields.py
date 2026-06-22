"""Rasterize the leyline network into per-cell magic fields.

Phase 4 step 5.  Every cell measures its distance to the nearest leyline
*segment* (point-to-segment under minimum-image), then:

* ``magic_strength`` = exponential falloff from the web + a tighter nexus bump
  + a low FBm floor so dead zones still flicker.
* ``magic_valence`` / ``magic_channels`` = inverse-distance-weighted blend over
  the nearest segments, each segment's aspect interpolated along its length by
  the projection ``t``, faded toward neutral where the magic is weak.

The hot path vectorizes **cells per segment** (≈n × segments, never n²).
"""

import numpy as np

from src.worldgen.config.worldgen_config import LeylineConfig
from src.worldgen.features import LeylineNetwork
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array


def _min_image(delta: Float64Array, width: float, height: float) -> Float64Array:
    """Minimum-image-correct an ``(..., 2)`` displacement array in place-safe copy."""
    out: Float64Array = np.array(delta, dtype=np.float64)
    out[..., 0] -= width * np.round(out[..., 0] / width)
    out[..., 1] -= height * np.round(out[..., 1] / height)
    return out


def rasterize_magic(
    *,
    geometry: MeshGeometry,
    network: LeylineNetwork,
    cfg: LeylineConfig,
    floor_noise: FractalField,
) -> tuple[Float64Array, Float64Array, Float64Array]:
    """Per-cell ``(magic_strength, magic_valence, magic_channels)`` from the web.

    Args:
        geometry: Torus mesh with sites and dimensions.
        network: The leyline network (nexus cells, aspects, edges).
        cfg: Leyline configuration (reaches, IDW knobs, floor noise).
        floor_noise: Low FBm field for the magic floor.

    Returns:
        magic_strength: Per-cell intensity in [0, 1].
        magic_valence: Per-cell valence in [-1, 1].
        magic_channels: Per-cell channel composition, shape ``(n, 3)``.
    """
    n: int = geometry.n_cells
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    span: float = max(width, height)
    third: float = 1.0 / 3.0

    # --- magic floor (always present) ---
    floor: Float64Array = (
        cfg.floor_strength
        * (
            floor_noise.sample_array(
                xs=sites[:, 0], ys=sites[:, 1], frequency=cfg.floor_frequency
            )
            + 1.0
        )
        * 0.5
    )

    uniform_channels: Float64Array = np.full((n, 3), third, dtype=np.float64)
    k: int = len(network.nexus_cells)
    if k == 0:
        strength: Float64Array = np.clip(floor, 0.0, 1.0)
        return strength, np.zeros(n, dtype=np.float64), uniform_channels

    nexus_sites: Float64Array = sites[network.nexus_cells]  # (k, 2)
    line_reach: float = cfg.line_reach * span
    nexus_reach: float = cfg.nexus_reach * span

    # --- distance to the nearest nexus point (for the bump) ---
    nexus_min: Float64Array = np.full(n, np.inf, dtype=np.float64)
    idx: int
    for idx in range(k):
        d: Float64Array = _min_image(sites - nexus_sites[idx], width, height)
        nexus_min = np.minimum(nexus_min, np.hypot(d[:, 0], d[:, 1]))
    nexus_bump: Float64Array = cfg.nexus_boost * np.exp(-nexus_min / nexus_reach)

    edges: list[tuple[int, int]] = network.edges
    n_seg: int = len(edges)
    if n_seg == 0:
        # A single isolated nexus: strength is the bump + floor only.
        strength = np.clip(nexus_bump + floor, 0.0, 1.0)
        return strength, np.zeros(n, dtype=np.float64), uniform_channels

    # --- per-segment distance and projection t (cells vectorized per segment) ---
    seg_dist: Float64Array = np.empty((n_seg, n), dtype=np.float64)
    seg_t: Float64Array = np.empty((n_seg, n), dtype=np.float64)
    seg: int
    for seg, (ia, ib) in enumerate(edges):
        a: Float64Array = nexus_sites[ia]
        ab: Float64Array = _min_image(nexus_sites[ib] - a, width, height)
        ab_len2: float = float(ab[0] * ab[0] + ab[1] * ab[1])
        ap: Float64Array = _min_image(sites - a, width, height)  # (n, 2)
        if ab_len2 < 1e-12:
            seg_dist[seg] = np.hypot(ap[:, 0], ap[:, 1])
            seg_t[seg] = 0.0
            continue
        t: Float64Array = np.clip((ap @ ab) / ab_len2, 0.0, 1.0)  # (n,)
        closest: Float64Array = ap - t[:, None] * ab[None, :]
        seg_dist[seg] = np.hypot(closest[:, 0], closest[:, 1])
        seg_t[seg] = t

    min_dist: Float64Array = seg_dist.min(axis=0)  # (n,)
    strength = np.clip(
        np.exp(-min_dist / line_reach) + nexus_bump + floor, 0.0, 1.0
    )

    # --- IDW over the k nearest segments ---
    dist_by_cell: Float64Array = seg_dist.T  # (n, n_seg)
    t_by_cell: Float64Array = seg_t.T  # (n, n_seg)
    w: Float64Array = 1.0 / (dist_by_cell + cfg.idw_epsilon)
    if n_seg > cfg.idw_k:
        # Zero out all but the idw_k largest weights per cell.
        kth: Float64Array = np.partition(
            w, n_seg - cfg.idw_k, axis=1
        )[:, n_seg - cfg.idw_k][:, None]
        w = np.where(w >= kth, w, 0.0)
    w_sum: Float64Array = w.sum(axis=1)  # (n,)
    safe_sum: Float64Array = np.where(w_sum > 0.0, w_sum, 1.0)

    ia_arr: Float64Array = np.array([e[0] for e in edges], dtype=np.int64)
    ib_arr: Float64Array = np.array([e[1] for e in edges], dtype=np.int64)

    # Valence: lerp endpoint valences by t, then IDW blend.
    val_a: Float64Array = network.nexus_valence[ia_arr]  # (n_seg,)
    val_b: Float64Array = network.nexus_valence[ib_arr]
    seg_valence: Float64Array = (
        (1.0 - t_by_cell) * val_a[None, :] + t_by_cell * val_b[None, :]
    )  # (n, n_seg)
    valence_raw: Float64Array = (w * seg_valence).sum(axis=1) / safe_sum

    # Channels: lerp endpoint channels by t, then IDW blend.
    chan_a: Float64Array = network.nexus_channels[ia_arr]  # (n_seg, 3)
    chan_b: Float64Array = network.nexus_channels[ib_arr]
    seg_channels: Float64Array = (
        (1.0 - t_by_cell)[:, :, None] * chan_a[None, :, :]
        + t_by_cell[:, :, None] * chan_b[None, :, :]
    )  # (n, n_seg, 3)
    channels_raw: Float64Array = (w[:, :, None] * seg_channels).sum(
        axis=1
    ) / safe_sum[:, None]

    # --- fade toward neutral where magic is weak ---
    magic_valence: Float64Array = valence_raw * strength
    magic_channels: Float64Array = third + (channels_raw - third) * strength[:, None]
    chan_sum: Float64Array = magic_channels.sum(axis=1, keepdims=True)
    magic_channels = np.divide(
        magic_channels,
        chan_sum,
        out=np.full_like(magic_channels, third),
        where=chan_sum > 0.0,
    )

    return strength, magic_valence, magic_channels
